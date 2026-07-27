from contextlib import asynccontextmanager
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.admin_ui import ADMIN_HTML
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
)
from app.seed import seed_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as session:
        await seed_database(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="Онлайн-база стоек ЧПУ, станков, операций и API Telegram-бота.",
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
    }


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page() -> str:
    return ADMIN_HTML


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
