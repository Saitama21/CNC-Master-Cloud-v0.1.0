from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ManufacturerBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=100)
    website_url: str | None = None
    active: bool = True


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerOut(ManufacturerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ControllerBase(BaseModel):
    manufacturer_id: int
    name: str = Field(min_length=2, max_length=160)
    family: str | None = None
    machine_types: list[str] = Field(default_factory=list)
    software_versions: list[str] = Field(default_factory=list)
    description: str | None = None
    active: bool = True


class ControllerCreate(ControllerBase):
    pass


class ControllerOut(ControllerBase):
    id: int
    manufacturer: ManufacturerOut | None = None
    model_config = ConfigDict(from_attributes=True)


class CNCCodeBase(BaseModel):
    controller_id: int
    code_type: str = Field(pattern="^[GMgm]$")
    code: str = Field(min_length=1, max_length=30)
    title: str = Field(min_length=2, max_length=250)
    description: str = Field(min_length=2)
    syntax: str | None = None
    example: str | None = None
    safety_notes: str | None = None
    source_url: str | None = None
    verification_status: str = "needs_review"
    active: bool = True


class CNCCodeCreate(CNCCodeBase):
    pass


class CNCCodeUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    syntax: str | None = None
    example: str | None = None
    safety_notes: str | None = None
    source_url: str | None = None
    verification_status: str | None = None
    active: bool | None = None


class CNCCodeOut(CNCCodeBase):
    id: int
    last_verified_at: datetime | None = None
    controller: ControllerOut | None = None
    model_config = ConfigDict(from_attributes=True)


class MaterialBase(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    name: str = Field(min_length=2, max_length=200)
    iso_group: str | None = None
    vc_min: float | None = None
    vc_max: float | None = None
    notes: str | None = None
    active: bool = True


class MaterialCreate(MaterialBase):
    pass


class MaterialOut(MaterialBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserUpsert(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str
    language_code: str | None = None


class UserOut(UserUpsert):
    id: int
    model_config = ConfigDict(from_attributes=True)


class MachineProfileCreate(BaseModel):
    telegram_id: int
    controller_id: int
    name: str = Field(min_length=1, max_length=150)
    machine_type: str = Field(min_length=2, max_length=80)
    machine_brand: str | None = None
    machine_model: str | None = None
    axes: str | None = None
    software_version: str | None = None
    max_rpm: int | None = Field(default=None, ge=1)
    driven_tools: bool = False
    notes: str | None = None


class MachineProfileOut(BaseModel):
    id: int
    controller_id: int
    name: str
    machine_type: str
    machine_brand: str | None = None
    machine_model: str | None = None
    axes: str | None = None
    software_version: str | None = None
    max_rpm: int | None = None
    driven_tools: bool
    notes: str | None = None
    controller: ControllerOut | None = None
    model_config = ConfigDict(from_attributes=True)


class MachiningOperationCreate(BaseModel):
    telegram_id: int
    machine_id: int
    operation_type: str = Field(min_length=2, max_length=60)
    title: str = Field(min_length=2, max_length=200)
    material_code: str | None = Field(default=None, max_length=60)
    details: str = Field(min_length=2, max_length=3000)
    parameters: dict[str, Any] = Field(default_factory=dict)


class MachiningOperationOut(BaseModel):
    id: int
    machine_profile_id: int
    operation_type: str
    title: str
    material_code: str | None = None
    details: str
    parameters: dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AdminStats(BaseModel):
    manufacturers: int
    controllers: int
    codes: int
    materials: int
    users: int
    machine_profiles: int
    operations: int
    catalog_items: int
    policies: int
    saved_tools: int
    process_plans: int


class ToolCatalogItemOut(BaseModel):
    key: str
    category: str
    subcategory: str
    name: str
    code: str
    operation_tags: list[str]
    iso_groups: list[str]
    dimensions: str
    description: str
    compatibility: str
    grade_hint: str
    source: str


class CustomToolItemCreate(ToolCatalogItemOut):
    active: bool = True


class SavedToolCreate(BaseModel):
    telegram_id: int
    machine_id: int
    tool_key: str
    tool_snapshot: dict[str, Any]


class SavedToolOut(BaseModel):
    id: int
    machine_profile_id: int
    tool_key: str
    tool_snapshot: dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProcessPlanCreate(BaseModel):
    telegram_id: int
    machine_id: int
    title: str = Field(min_length=2, max_length=250)
    material_code: str | None = None
    operations: list[dict[str, Any]] = Field(min_length=1)


class ProcessPlanOut(BaseModel):
    id: int
    machine_profile_id: int
    title: str
    material_code: str | None = None
    operations: list[dict[str, Any]]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UsageConsume(BaseModel):
    telegram_id: int
    feature_key: str = Field(min_length=2, max_length=80)
    consume: bool = True


class UsageDecision(BaseModel):
    allowed: bool
    feature_key: str
    title: str
    reason: str | None = None
    limit_per_hour: int | None = None
    used: int = 0
    remaining: int | None = None
    reset_at: datetime | None = None


class FeaturePolicyBase(BaseModel):
    feature_key: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=160)
    enabled: bool = True
    limit_per_hour: int | None = Field(default=None, ge=0, le=100000)
    allowed_start_hour: int | None = Field(default=None, ge=0, le=23)
    allowed_end_hour: int | None = Field(default=None, ge=0, le=23)
    timezone: str = "Europe/Kyiv"


class FeaturePolicyOut(FeaturePolicyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class UserFeatureOverrideCreate(BaseModel):
    telegram_id: int
    feature_key: str
    enabled: bool | None = None
    limit_per_hour: int | None = Field(default=None, ge=0, le=100000)
    allowed_start_hour: int | None = Field(default=None, ge=0, le=23)
    allowed_end_hour: int | None = Field(default=None, ge=0, le=23)
    unlimited: bool = False
    note: str | None = None


class UserFeatureOverrideOut(BaseModel):
    id: int
    feature_key: str
    enabled: bool | None = None
    limit_per_hour: int | None = None
    allowed_start_hour: int | None = None
    allowed_end_hour: int | None = None
    unlimited: bool
    note: str | None = None
    model_config = ConfigDict(from_attributes=True)


class AdminUserOut(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    full_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ClientGenerateRequest(BaseModel):
    telegram_id: int = 0
    machine_id: int = 0
    title: str = Field(default="CNC project", min_length=1, max_length=250)
    machine: dict[str, Any] = Field(default_factory=dict)
    stock: dict[str, Any]
    contour: dict[str, Any]
    operations: list[dict[str, Any]] = Field(min_length=1)


class ClientProjectCreate(BaseModel):
    telegram_id: int
    machine_id: int
    title: str = Field(min_length=1, max_length=250)
    payload: dict[str, Any]
    generated: dict[str, Any] | None = None


class ClientProjectOut(BaseModel):
    id: int
    machine_profile_id: int
    title: str
    payload: dict[str, Any]
    generated: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
