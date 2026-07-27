from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import FeaturePolicy, FeatureUsage, User, UserFeatureOverride


FEATURES = {
    "tool_selector": "Подбор инструмента",
    "tool_catalog": "Каталог инструмента",
    "multi_operations": "Несколько операций",
    "calculators": "Калькуляторы",
    "gcode_check": "Проверка G-кода",
    "alarms": "Ошибки стойки",
    "process": "Техпроцесс",
    "codes": "G/M-коды",
    "engineering_client": "Инженерный CNC-клиент",
    "pdf_scan": "Сканирование чертежа PDF",
    "gcode_generate": "Расчёт и генерация G-кода",
}

DEFAULT_LIMITS = {
    "tool_selector": 30,
    "tool_catalog": 100,
    "multi_operations": 10,
    "calculators": 60,
    "gcode_check": 20,
    "alarms": 30,
    "process": 20,
    "codes": 100,
    "engineering_client": 30,
    "pdf_scan": 10,
    "gcode_generate": 20,
}


def admin_ids() -> set[int]:
    result: set[int] = set()
    for item in settings.admin_telegram_ids.split(","):
        item = item.strip()
        if item.isdigit():
            result.add(int(item))
    return result


async def ensure_default_policies(session: AsyncSession) -> None:
    existing = set(await session.scalars(select(FeaturePolicy.feature_key)))
    for key, title in FEATURES.items():
        if key not in existing:
            session.add(FeaturePolicy(
                feature_key=key,
                title=title,
                enabled=True,
                limit_per_hour=DEFAULT_LIMITS.get(key),
                timezone=settings.default_timezone,
            ))
    await session.commit()


def _within_window(hour: int, start: int | None, end: int | None) -> bool:
    if start is None or end is None or start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


async def consume_feature(
    session: AsyncSession,
    *,
    telegram_id: int,
    feature_key: str,
    consume: bool = True,
) -> dict:
    title = FEATURES.get(feature_key, feature_key)
    if telegram_id in admin_ids():
        return {
            "allowed": True, "feature_key": feature_key, "title": title,
            "reason": "Администратор: без лимита", "limit_per_hour": None,
            "used": 0, "remaining": None, "reset_at": None,
        }

    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        return {
            "allowed": False, "feature_key": feature_key, "title": title,
            "reason": "Пользователь ещё не зарегистрирован. Отправьте /start.",
            "limit_per_hour": None, "used": 0, "remaining": None, "reset_at": None,
        }

    policy = await session.scalar(select(FeaturePolicy).where(FeaturePolicy.feature_key == feature_key))
    if policy is None:
        policy = FeaturePolicy(
            feature_key=feature_key, title=title, enabled=True,
            limit_per_hour=DEFAULT_LIMITS.get(feature_key), timezone=settings.default_timezone,
        )
        session.add(policy)
        await session.flush()

    override = await session.scalar(
        select(UserFeatureOverride).where(
            UserFeatureOverride.user_id == user.id,
            UserFeatureOverride.feature_key == feature_key,
        )
    )

    enabled = override.enabled if override and override.enabled is not None else policy.enabled
    unlimited = bool(override and override.unlimited)
    limit = override.limit_per_hour if override and override.limit_per_hour is not None else policy.limit_per_hour
    start = override.allowed_start_hour if override and override.allowed_start_hour is not None else policy.allowed_start_hour
    end = override.allowed_end_hour if override and override.allowed_end_hour is not None else policy.allowed_end_hour
    tz_name = policy.timezone or settings.default_timezone
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = timezone.utc

    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(tz)
    reset_at = (now_utc.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))

    if not enabled:
        return {
            "allowed": False, "feature_key": feature_key, "title": policy.title,
            "reason": "Функция отключена администратором.", "limit_per_hour": limit,
            "used": 0, "remaining": 0, "reset_at": reset_at,
        }
    if not _within_window(local_now.hour, start, end):
        window = f"{start:02d}:00–{end:02d}:00" if start is not None and end is not None else "заданное время"
        return {
            "allowed": False, "feature_key": feature_key, "title": policy.title,
            "reason": f"Функция доступна только {window} ({tz_name}).",
            "limit_per_hour": limit, "used": 0, "remaining": 0, "reset_at": reset_at,
        }
    if unlimited or limit is None:
        return {
            "allowed": True, "feature_key": feature_key, "title": policy.title,
            "reason": "Безлимитный доступ", "limit_per_hour": None,
            "used": 0, "remaining": None, "reset_at": reset_at,
        }
    if limit == 0:
        return {
            "allowed": False, "feature_key": feature_key, "title": policy.title,
            "reason": "Лимит установлен в 0 использований в час.",
            "limit_per_hour": 0, "used": 0, "remaining": 0, "reset_at": reset_at,
        }

    bucket = now_utc.replace(minute=0, second=0, microsecond=0)
    usage = await session.scalar(
        select(FeatureUsage).where(
            FeatureUsage.user_id == user.id,
            FeatureUsage.feature_key == feature_key,
            FeatureUsage.bucket_start == bucket,
        )
    )
    used = usage.count if usage else 0
    if used >= limit:
        return {
            "allowed": False, "feature_key": feature_key, "title": policy.title,
            "reason": f"Часовой лимит исчерпан: {used}/{limit}.",
            "limit_per_hour": limit, "used": used, "remaining": 0, "reset_at": reset_at,
        }

    if consume:
        if usage is None:
            usage = FeatureUsage(
                user_id=user.id, feature_key=feature_key, bucket_start=bucket, count=1
            )
            session.add(usage)
            used = 1
        else:
            usage.count += 1
            used = usage.count
        await session.commit()

    return {
        "allowed": True, "feature_key": feature_key, "title": policy.title,
        "reason": None, "limit_per_hour": limit, "used": used,
        "remaining": max(0, limit - used), "reset_at": reset_at,
    }
