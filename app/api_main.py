from contextlib import asynccontextmanager
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin_ui import ADMIN_HTML
from app.client_ui import CLIENT_HTML
from app.cnc_client import ClientValidationError, analyze_pdf_bytes, analyze_image_bytes, generate_engineering_plan
from app.openai_drawing import analyze_drawing_region_with_openai
from app.catalog_data import CATEGORY_LABELS, catalog_count, get_item, search_catalog
from app.config import settings
from app.db import SessionLocal, get_session, init_db
from app.models import (
    CNCCode,
    ControllerModel,
    MachineProfile,
    MachiningOperation,
    Manufacturer,
    Material,
    User,
    CustomToolItem,
    FeaturePolicy,
    ProcessPlan,
    SavedTool,
    UserFeatureOverride,
    ClientProject,
)
from app.schemas import (
    AdminStats,
    CNCCodeCreate,
    CNCCodeOut,
    CNCCodeUpdate,
    ControllerCreate,
    ControllerOut,
    MachineProfileCreate,
    MachineProfileOut,
    MachiningOperationCreate,
    MachiningOperationOut,
    ManufacturerCreate,
    ManufacturerOut,
    MaterialCreate,
    MaterialOut,
    UserOut,
    UserUpsert,
    AdminUserOut,
    CustomToolItemCreate,
    FeaturePolicyBase,
    FeaturePolicyOut,
    ProcessPlanCreate,
    ProcessPlanOut,
    SavedToolCreate,
    SavedToolOut,
    ToolCatalogItemOut,
    UsageConsume,
    UsageDecision,
    UserFeatureOverrideCreate,
    UserFeatureOverrideOut,
    ClientGenerateRequest,
    ClientProjectCreate,
    ClientProjectOut,
)
from app.seed import seed_database
from app.usage_limits import consume_feature, ensure_default_policies


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as session:
        await seed_database(session)
        await ensure_default_policies(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.5.1",
    description="CNC Master Cloud Engineering Client: Drawing Intelligence, PDF/фото, инженерная геометрия, Stock Removal и SINUMERIK 828D.",
    lifespan=lifespan,
)


async def require_admin(
    x_admin_key: Annotated[str | None, Header()] = None,
) -> None:
    if not x_admin_key or not secrets.compare_digest(x_admin_key, settings.admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin key")


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "status": "online",
        "docs": "/docs",
        "admin": "/admin",
        "client": "/client",
    }


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page() -> str:
    return ADMIN_HTML


@app.get("/client", response_class=HTMLResponse, include_in_schema=False)
async def engineering_client_page() -> str:
    return CLIENT_HTML


async def _require_feature(
    session: AsyncSession, telegram_id: int, feature_key: str, *, consume: bool = True
) -> dict:
    if telegram_id <= 0:
        raise HTTPException(status_code=422, detail="Укажите цифровой Telegram ID.")
    decision = await consume_feature(
        session, telegram_id=telegram_id, feature_key=feature_key, consume=consume
    )
    if not decision.get("allowed"):
        raise HTTPException(status_code=429, detail=decision.get("reason") or "Функция недоступна")
    return decision


@app.post("/api/v1/client/pdf/analyze", tags=["engineering-client"])
async def client_analyze_pdf(
    file: UploadFile = File(...),
    page_number: int = Form(default=1),
    telegram_id: int = Form(default=0),
    crop_x: float | None = Form(default=None),
    crop_y: float | None = Form(default=None),
    crop_w: float | None = Form(default=None),
    crop_h: float | None = Form(default=None),
    rotation: int = Form(default=0),
    profile_type: str = Form(default="outer"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await _require_feature(session, telegram_id, "pdf_scan")
    supported_images = {"image/png", "image/jpeg", "image/webp"}
    if file.content_type not in {"application/pdf", "application/octet-stream", *supported_images}:
        raise HTTPException(status_code=415, detail="Загрузите PDF, PNG, JPG или WEBP.")
    data = await file.read()
    try:
        if file.content_type in supported_images:
            return analyze_image_bytes(data, rotation=rotation, profile_type=profile_type)
        crop = None
        if None not in {crop_x, crop_y, crop_w, crop_h}:
            crop = (float(crop_x), float(crop_y), float(crop_w), float(crop_h))
        return analyze_pdf_bytes(data, page_number, crop=crop, rotation=rotation, profile_type=profile_type)
    except ClientValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/client/ai/region", tags=["engineering-client"])
async def client_ai_region(
    image: UploadFile = File(...),
    telegram_id: int = Form(default=0),
    profile_type: str = Form(default="outer"),
    x_mode: str = Form(default="diameter"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await _require_feature(session, telegram_id, "pdf_scan")
    if image.content_type not in {"image/png", "image/jpeg", "image/webp", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Для AI-анализа нужна PNG, JPG или WEBP область.")
    data = await image.read()
    if not data or len(data) > 12 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Выбранная область пуста или больше 12 МБ.")
    import base64
    mime = image.content_type if image.content_type and image.content_type.startswith("image/") else "image/png"
    image_data_url = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
    try:
        return await analyze_drawing_region_with_openai(
            image_data_url, profile_type=profile_type, x_mode=x_mode
        )
    except ClientValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/client/generate", tags=["engineering-client"])
async def client_generate(
    payload: ClientGenerateRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    await _require_feature(session, payload.telegram_id, "gcode_generate")
    if payload.machine_id > 0:
        machine = await session.scalar(
            select(MachineProfile).join(User).where(
                MachineProfile.id == payload.machine_id,
                User.telegram_id == payload.telegram_id,
            )
        )
        if machine is None:
            raise HTTPException(status_code=404, detail="Станок пользователя не найден.")
    try:
        return generate_engineering_plan(payload.model_dump())
    except ClientValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/v1/client/projects", response_model=ClientProjectOut, tags=["engineering-client"]
)
async def create_client_project(
    payload: ClientProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> ClientProject:
    await _require_feature(session, payload.telegram_id, "engineering_client")
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    machine = await session.scalar(
        select(MachineProfile).join(User).where(
            MachineProfile.id == payload.machine_id,
            User.telegram_id == payload.telegram_id,
        )
    )
    if user is None or machine is None:
        raise HTTPException(status_code=404, detail="Пользователь или станок не найден.")
    item = ClientProject(
        user_id=user.id,
        machine_profile_id=machine.id,
        title=payload.title,
        payload=payload.payload,
        generated=payload.generated,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@app.get(
    "/api/v1/users/{telegram_id}/machines/{machine_id}/client-projects",
    response_model=list[ClientProjectOut],
    tags=["engineering-client"],
)
async def list_client_projects(
    telegram_id: int, machine_id: int, session: AsyncSession = Depends(get_session)
) -> list[ClientProject]:
    machine = await session.scalar(
        select(MachineProfile).join(User).where(
            MachineProfile.id == machine_id, User.telegram_id == telegram_id
        )
    )
    if machine is None:
        raise HTTPException(status_code=404, detail="Станок не найден.")
    result = await session.scalars(
        select(ClientProject)
        .where(ClientProject.machine_profile_id == machine_id)
        .order_by(ClientProject.updated_at.desc(), ClientProject.id.desc())
    )
    return list(result)


@app.get(
    "/api/v1/users/{telegram_id}/client-projects/{project_id}",
    response_model=ClientProjectOut,
    tags=["engineering-client"],
)
async def get_client_project(
    telegram_id: int, project_id: int, session: AsyncSession = Depends(get_session)
) -> ClientProject:
    item = await session.scalar(
        select(ClientProject).join(User, ClientProject.user_id == User.id).where(
            ClientProject.id == project_id, User.telegram_id == telegram_id
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    return item



@app.get(
    "/api/v1/manufacturers",
    response_model=list[ManufacturerOut],
    tags=["catalog"],
)
async def list_manufacturers(
    session: AsyncSession = Depends(get_session),
) -> list[Manufacturer]:
    result = await session.scalars(
        select(Manufacturer)
        .where(Manufacturer.active.is_(True))
        .order_by(Manufacturer.name)
    )
    return list(result)


@app.get(
    "/api/v1/controllers",
    response_model=list[ControllerOut],
    tags=["catalog"],
)
async def list_controllers(
    manufacturer_id: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[ControllerModel]:
    stmt = (
        select(ControllerModel)
        .options(selectinload(ControllerModel.manufacturer))
        .where(ControllerModel.active.is_(True))
        .order_by(ControllerModel.name)
    )
    if manufacturer_id is not None:
        stmt = stmt.where(ControllerModel.manufacturer_id == manufacturer_id)
    result = await session.scalars(stmt)
    return list(result)


@app.get(
    "/api/v1/controllers/{controller_id}",
    response_model=ControllerOut,
    tags=["catalog"],
)
async def get_controller(
    controller_id: int,
    session: AsyncSession = Depends(get_session),
) -> ControllerModel:
    item = await session.scalar(
        select(ControllerModel)
        .options(selectinload(ControllerModel.manufacturer))
        .where(ControllerModel.id == controller_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Controller not found")
    return item


@app.get(
    "/api/v1/codes/search",
    response_model=list[CNCCodeOut],
    tags=["catalog"],
)
async def search_codes(
    q: str = Query(min_length=1, max_length=100),
    controller_id: int | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[CNCCode]:
    normalized = q.strip().upper().replace(" ", "")
    contains = f"%{q.strip()}%"
    stmt = (
        select(CNCCode)
        .options(
            selectinload(CNCCode.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(
            CNCCode.active.is_(True),
            or_(
                func.upper(CNCCode.code) == normalized,
                CNCCode.title.ilike(contains),
                CNCCode.description.ilike(contains),
            ),
        )
        .order_by(CNCCode.code, CNCCode.controller_id)
        .limit(limit)
    )
    if controller_id is not None:
        stmt = stmt.where(CNCCode.controller_id == controller_id)
    result = await session.scalars(stmt)
    return list(result.unique())


@app.get(
    "/api/v1/materials",
    response_model=list[MaterialOut],
    tags=["catalog"],
)
async def list_materials(
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Material]:
    stmt = select(Material).where(Material.active.is_(True)).order_by(Material.name)
    if q:
        contains = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Material.code.ilike(contains),
                Material.name.ilike(contains),
                Material.iso_group.ilike(contains),
            )
        )
    result = await session.scalars(stmt)
    return list(result)


@app.post(
    "/api/v1/users/upsert",
    response_model=UserOut,
    tags=["users"],
)
async def upsert_user(
    payload: UserUpsert,
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.scalar(
        select(User).where(User.telegram_id == payload.telegram_id)
    )
    if user is None:
        user = User(**payload.model_dump())
        session.add(user)
    else:
        for field, value in payload.model_dump().items():
            setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


@app.get(
    "/api/v1/users/{telegram_id}/machines",
    response_model=list[MachineProfileOut],
    tags=["machines"],
)
async def list_user_machines(
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MachineProfile]:
    result = await session.scalars(
        select(MachineProfile)
        .join(User)
        .options(
            selectinload(MachineProfile.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(User.telegram_id == telegram_id)
        .order_by(MachineProfile.created_at.desc())
    )
    return list(result)


@app.post(
    "/api/v1/machines",
    response_model=MachineProfileOut,
    tags=["machines"],
)
async def create_machine(
    payload: MachineProfileCreate,
    session: AsyncSession = Depends(get_session),
) -> MachineProfile:
    user = await session.scalar(
        select(User).where(User.telegram_id == payload.telegram_id)
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found; call users/upsert")

    controller = await session.get(ControllerModel, payload.controller_id)
    if controller is None:
        raise HTTPException(status_code=404, detail="Controller not found")

    values = payload.model_dump(exclude={"telegram_id"})
    item = MachineProfile(user_id=user.id, **values)
    session.add(item)
    await session.commit()

    return await session.scalar(
        select(MachineProfile)
        .options(
            selectinload(MachineProfile.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(MachineProfile.id == item.id)
    )



@app.get(
    "/api/v1/users/{telegram_id}/machines/{machine_id}",
    response_model=MachineProfileOut,
    tags=["machines"],
)
async def get_user_machine(
    telegram_id: int,
    machine_id: int,
    session: AsyncSession = Depends(get_session),
) -> MachineProfile:
    item = await session.scalar(
        select(MachineProfile)
        .join(User)
        .options(
            selectinload(MachineProfile.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(
            MachineProfile.id == machine_id,
            User.telegram_id == telegram_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    return item


@app.get(
    "/api/v1/users/{telegram_id}/machines/{machine_id}/operations",
    response_model=list[MachiningOperationOut],
    tags=["operations"],
)
async def list_operations(
    telegram_id: int,
    machine_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[MachiningOperation]:
    machine = await session.scalar(
        select(MachineProfile)
        .join(User)
        .where(
            MachineProfile.id == machine_id,
            User.telegram_id == telegram_id,
        )
    )
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    result = await session.scalars(
        select(MachiningOperation)
        .where(MachiningOperation.machine_profile_id == machine_id)
        .order_by(MachiningOperation.created_at, MachiningOperation.id)
    )
    return list(result)


@app.post(
    "/api/v1/operations",
    response_model=MachiningOperationOut,
    tags=["operations"],
)
async def create_operation(
    payload: MachiningOperationCreate,
    session: AsyncSession = Depends(get_session),
) -> MachiningOperation:
    machine = await session.scalar(
        select(MachineProfile)
        .join(User)
        .where(
            MachineProfile.id == payload.machine_id,
            User.telegram_id == payload.telegram_id,
        )
    )
    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    values = payload.model_dump(exclude={"telegram_id", "machine_id"})
    item = MachiningOperation(machine_profile_id=payload.machine_id, **values)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@app.delete(
    "/api/v1/users/{telegram_id}/operations/{operation_id}",
    tags=["operations"],
)
async def delete_operation(
    telegram_id: int,
    operation_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    item = await session.scalar(
        select(MachiningOperation)
        .join(MachineProfile)
        .join(User)
        .where(
            MachiningOperation.id == operation_id,
            User.telegram_id == telegram_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    await session.delete(item)
    await session.commit()
    return {"deleted": True}


@app.delete("/api/v1/users/{telegram_id}/machines/{machine_id}", tags=["machines"])
async def delete_machine(
    telegram_id: int,
    machine_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    item = await session.scalar(
        select(MachineProfile)
        .join(User)
        .where(
            MachineProfile.id == machine_id,
            User.telegram_id == telegram_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Machine not found")
    await session.delete(item)
    await session.commit()
    return {"deleted": True}


@app.get(
    "/api/v1/admin/stats",
    response_model=AdminStats,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_stats(
    session: AsyncSession = Depends(get_session),
) -> AdminStats:
    async def count(model) -> int:
        return int(await session.scalar(select(func.count()).select_from(model)) or 0)

    return AdminStats(
        manufacturers=await count(Manufacturer),
        controllers=await count(ControllerModel),
        codes=await count(CNCCode),
        materials=await count(Material),
        users=await count(User),
        machine_profiles=await count(MachineProfile),
        operations=await count(MachiningOperation),
        catalog_items=catalog_count() + await count(CustomToolItem),
        policies=await count(FeaturePolicy),
        saved_tools=await count(SavedTool),
        process_plans=await count(ProcessPlan),
    )


@app.post(
    "/api/v1/admin/manufacturers",
    response_model=ManufacturerOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_create_manufacturer(
    payload: ManufacturerCreate,
    session: AsyncSession = Depends(get_session),
) -> Manufacturer:
    item = Manufacturer(**payload.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@app.post(
    "/api/v1/admin/controllers",
    response_model=ControllerOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_create_controller(
    payload: ControllerCreate,
    session: AsyncSession = Depends(get_session),
) -> ControllerModel:
    item = ControllerModel(**payload.model_dump())
    session.add(item)
    await session.commit()
    return await session.scalar(
        select(ControllerModel)
        .options(selectinload(ControllerModel.manufacturer))
        .where(ControllerModel.id == item.id)
    )


@app.post(
    "/api/v1/admin/codes",
    response_model=CNCCodeOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_create_code(
    payload: CNCCodeCreate,
    session: AsyncSession = Depends(get_session),
) -> CNCCode:
    values = payload.model_dump()
    values["code_type"] = values["code_type"].upper()
    values["code"] = values["code"].upper().replace(" ", "")
    item = CNCCode(**values)
    session.add(item)
    await session.commit()
    return await session.scalar(
        select(CNCCode)
        .options(
            selectinload(CNCCode.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(CNCCode.id == item.id)
    )


@app.patch(
    "/api/v1/admin/codes/{code_id}",
    response_model=CNCCodeOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_update_code(
    code_id: int,
    payload: CNCCodeUpdate,
    session: AsyncSession = Depends(get_session),
) -> CNCCode:
    item = await session.get(CNCCode, code_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Code not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await session.commit()
    return await session.scalar(
        select(CNCCode)
        .options(
            selectinload(CNCCode.controller)
            .selectinload(ControllerModel.manufacturer)
        )
        .where(CNCCode.id == item.id)
    )


@app.post(
    "/api/v1/admin/materials",
    response_model=MaterialOut,
    dependencies=[Depends(require_admin)],
    tags=["admin"],
)
async def admin_create_material(
    payload: MaterialCreate,
    session: AsyncSession = Depends(get_session),
) -> Material:
    item = Material(**payload.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@app.get("/api/v1/tools/categories", tags=["tools"])
async def tool_categories() -> dict:
    return {"count": catalog_count(), "categories": CATEGORY_LABELS}


@app.get(
    "/api/v1/tools",
    response_model=list[ToolCatalogItemOut],
    tags=["tools"],
)
async def list_tools(
    category: str | None = None,
    operation: str | None = None,
    iso_group: str | None = None,
    q: str | None = None,
    page: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    items = [item.to_dict() for item in search_catalog(
        category=category, operation=operation, iso_group=iso_group, query=q
    )]
    custom_stmt = select(CustomToolItem).where(CustomToolItem.active.is_(True))
    if category:
        custom_stmt = custom_stmt.where(CustomToolItem.category == category)
    custom = list(await session.scalars(custom_stmt.order_by(CustomToolItem.name)))
    for item in custom:
        payload = {
            "key": item.key, "category": item.category, "subcategory": item.subcategory,
            "name": item.name, "code": item.code,
            "operation_tags": item.operation_tags or [], "iso_groups": item.iso_groups or [],
            "dimensions": item.dimensions, "description": item.description,
            "compatibility": item.compatibility, "grade_hint": item.grade_hint,
            "source": item.source,
        }
        if operation and operation not in payload["operation_tags"]:
            continue
        if iso_group and iso_group.upper() not in payload["iso_groups"]:
            continue
        if q and q.casefold() not in (payload["name"] + " " + payload["code"] + " " + payload["description"]).casefold():
            continue
        items.append(payload)
    start = page * limit
    return items[start:start + limit]


@app.get("/api/v1/tools/{tool_key}", response_model=ToolCatalogItemOut, tags=["tools"])
async def get_tool(tool_key: str, session: AsyncSession = Depends(get_session)) -> dict:
    item = get_item(tool_key)
    if item:
        return item.to_dict()
    custom = await session.scalar(
        select(CustomToolItem).where(CustomToolItem.key == tool_key.upper(), CustomToolItem.active.is_(True))
    )
    if custom is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "key": custom.key, "category": custom.category, "subcategory": custom.subcategory,
        "name": custom.name, "code": custom.code,
        "operation_tags": custom.operation_tags or [], "iso_groups": custom.iso_groups or [],
        "dimensions": custom.dimensions, "description": custom.description,
        "compatibility": custom.compatibility, "grade_hint": custom.grade_hint,
        "source": custom.source,
    }


@app.post("/api/v1/saved-tools", response_model=SavedToolOut, tags=["tools"])
async def save_tool(payload: SavedToolCreate, session: AsyncSession = Depends(get_session)) -> SavedTool:
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    machine = await session.scalar(
        select(MachineProfile).where(MachineProfile.id == payload.machine_id)
    )
    if user is None or machine is None or machine.user_id != user.id:
        raise HTTPException(status_code=404, detail="User or machine not found")
    item = await session.scalar(select(SavedTool).where(
        SavedTool.user_id == user.id,
        SavedTool.machine_profile_id == payload.machine_id,
        SavedTool.tool_key == payload.tool_key,
    ))
    if item is None:
        item = SavedTool(
            user_id=user.id, machine_profile_id=payload.machine_id,
            tool_key=payload.tool_key, tool_snapshot=payload.tool_snapshot,
        )
        session.add(item)
    else:
        item.tool_snapshot = payload.tool_snapshot
    await session.commit()
    await session.refresh(item)
    return item


@app.get(
    "/api/v1/users/{telegram_id}/machines/{machine_id}/saved-tools",
    response_model=list[SavedToolOut], tags=["tools"],
)
async def saved_tools(
    telegram_id: int, machine_id: int, session: AsyncSession = Depends(get_session)
) -> list[SavedTool]:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        return []
    result = await session.scalars(select(SavedTool).where(
        SavedTool.user_id == user.id, SavedTool.machine_profile_id == machine_id
    ).order_by(SavedTool.created_at.desc()))
    return list(result)


@app.post("/api/v1/process-plans", response_model=ProcessPlanOut, tags=["operations"])
async def create_process_plan(
    payload: ProcessPlanCreate, session: AsyncSession = Depends(get_session)
) -> ProcessPlan:
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    machine = await session.get(MachineProfile, payload.machine_id)
    if user is None or machine is None or machine.user_id != user.id:
        raise HTTPException(status_code=404, detail="User or machine not found")
    item = ProcessPlan(
        user_id=user.id, machine_profile_id=payload.machine_id,
        title=payload.title, material_code=payload.material_code,
        operations=payload.operations,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@app.get(
    "/api/v1/users/{telegram_id}/machines/{machine_id}/process-plans",
    response_model=list[ProcessPlanOut], tags=["operations"],
)
async def list_process_plans(
    telegram_id: int, machine_id: int, session: AsyncSession = Depends(get_session)
) -> list[ProcessPlan]:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        return []
    result = await session.scalars(select(ProcessPlan).where(
        ProcessPlan.user_id == user.id, ProcessPlan.machine_profile_id == machine_id
    ).order_by(ProcessPlan.created_at.desc()))
    return list(result)


@app.post("/api/v1/usage/consume", response_model=UsageDecision, tags=["usage"])
async def usage_consume(
    payload: UsageConsume, session: AsyncSession = Depends(get_session)
) -> dict:
    return await consume_feature(
        session,
        telegram_id=payload.telegram_id,
        feature_key=payload.feature_key,
        consume=payload.consume,
    )


@app.get(
    "/api/v1/admin/policies",
    response_model=list[FeaturePolicyOut],
    dependencies=[Depends(require_admin)], tags=["admin"],
)
async def admin_policies(session: AsyncSession = Depends(get_session)) -> list[FeaturePolicy]:
    result = await session.scalars(select(FeaturePolicy).order_by(FeaturePolicy.title))
    return list(result)


@app.put(
    "/api/v1/admin/policies/{feature_key}",
    response_model=FeaturePolicyOut,
    dependencies=[Depends(require_admin)], tags=["admin"],
)
async def admin_update_policy(
    feature_key: str, payload: FeaturePolicyBase, session: AsyncSession = Depends(get_session)
) -> FeaturePolicy:
    item = await session.scalar(select(FeaturePolicy).where(FeaturePolicy.feature_key == feature_key))
    values = payload.model_dump()
    values["feature_key"] = feature_key
    if item is None:
        item = FeaturePolicy(**values)
        session.add(item)
    else:
        for field, value in values.items():
            setattr(item, field, value)
    await session.commit()
    await session.refresh(item)
    return item


@app.get(
    "/api/v1/admin/users", response_model=list[AdminUserOut],
    dependencies=[Depends(require_admin)], tags=["admin"],
)
async def admin_users(
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if q:
        contains = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(contains), User.username.ilike(contains)))
    return list(await session.scalars(stmt))


@app.post(
    "/api/v1/admin/user-overrides",
    response_model=UserFeatureOverrideOut,
    dependencies=[Depends(require_admin)], tags=["admin"],
)
async def admin_user_override(
    payload: UserFeatureOverrideCreate, session: AsyncSession = Depends(get_session)
) -> UserFeatureOverride:
    user = await session.scalar(select(User).where(User.telegram_id == payload.telegram_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    item = await session.scalar(select(UserFeatureOverride).where(
        UserFeatureOverride.user_id == user.id,
        UserFeatureOverride.feature_key == payload.feature_key,
    ))
    values = payload.model_dump(exclude={"telegram_id"})
    if item is None:
        item = UserFeatureOverride(user_id=user.id, **values)
        session.add(item)
    else:
        for field, value in values.items():
            setattr(item, field, value)
    await session.commit()
    await session.refresh(item)
    return item


@app.post(
    "/api/v1/admin/tools", response_model=ToolCatalogItemOut,
    dependencies=[Depends(require_admin)], tags=["admin"],
)
async def admin_create_tool(
    payload: CustomToolItemCreate, session: AsyncSession = Depends(get_session)
) -> dict:
    if get_item(payload.key):
        raise HTTPException(status_code=409, detail="Key conflicts with built-in catalog")
    item = await session.scalar(select(CustomToolItem).where(CustomToolItem.key == payload.key.upper()))
    values = payload.model_dump()
    values["key"] = values["key"].upper()
    if item is None:
        item = CustomToolItem(**values)
        session.add(item)
    else:
        for field, value in values.items():
            setattr(item, field, value)
    await session.commit()
    return {
        "key": item.key, "category": item.category, "subcategory": item.subcategory,
        "name": item.name, "code": item.code,
        "operation_tags": item.operation_tags or [], "iso_groups": item.iso_groups or [],
        "dimensions": item.dimensions, "description": item.description,
        "compatibility": item.compatibility, "grade_hint": item.grade_hint,
        "source": item.source,
    }
