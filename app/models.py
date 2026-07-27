from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    controllers: Mapped[list[ControllerModel]] = relationship(
        back_populates="manufacturer",
        cascade="all, delete-orphan",
    )


class ControllerModel(Base):
    __tablename__ = "controller_models"
    __table_args__ = (
        UniqueConstraint("manufacturer_id", "name", name="uq_controller_mfr_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    manufacturer_id: Mapped[int] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), index=True)
    family: Mapped[str | None] = mapped_column(String(160), nullable=True)
    machine_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    software_versions: Mapped[list[str]] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    manufacturer: Mapped[Manufacturer] = relationship(back_populates="controllers")
    codes: Mapped[list[CNCCode]] = relationship(
        back_populates="controller",
        cascade="all, delete-orphan",
    )
    machine_profiles: Mapped[list[MachineProfile]] = relationship(
        back_populates="controller",
    )


class CNCCode(Base):
    __tablename__ = "cnc_codes"
    __table_args__ = (
        UniqueConstraint(
            "controller_id",
            "code_type",
            "code",
            name="uq_code_controller_type_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    controller_id: Mapped[int] = mapped_column(
        ForeignKey("controller_models.id", ondelete="CASCADE"),
        index=True,
    )
    code_type: Mapped[str] = mapped_column(String(1), index=True)
    code: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(250), index=True)
    description: Mapped[str] = mapped_column(Text)
    syntax: Mapped[str | None] = mapped_column(Text, nullable=True)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30),
        default="needs_review",
        index=True,
    )
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    controller: Mapped[ControllerModel] = relationship(back_populates="codes")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    iso_group: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    vc_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    vc_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(250))
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    machine_profiles: Mapped[list[MachineProfile]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class MachineProfile(Base):
    __tablename__ = "machine_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    controller_id: Mapped[int] = mapped_column(
        ForeignKey("controller_models.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150))
    machine_type: Mapped[str] = mapped_column(String(80), index=True)
    machine_brand: Mapped[str | None] = mapped_column(String(150), nullable=True)
    machine_model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    axes: Mapped[str | None] = mapped_column(String(100), nullable=True)
    software_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_rpm: Mapped[int | None] = mapped_column(nullable=True)
    driven_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="machine_profiles")
    controller: Mapped[ControllerModel] = relationship(
        back_populates="machine_profiles",
    )
    operations: Mapped[list[MachiningOperation]] = relationship(
        back_populates="machine",
        cascade="all, delete-orphan",
    )


class MachiningOperation(Base):
    __tablename__ = "machining_operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    machine_profile_id: Mapped[int] = mapped_column(
        ForeignKey("machine_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    operation_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(200))
    material_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    details: Mapped[str] = mapped_column(Text)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    machine: Mapped[MachineProfile] = relationship(back_populates="operations")


class FeaturePolicy(Base):
    __tablename__ = "feature_policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    feature_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    limit_per_hour: Mapped[int | None] = mapped_column(nullable=True)
    allowed_start_hour: Mapped[int | None] = mapped_column(nullable=True)
    allowed_end_hour: Mapped[int | None] = mapped_column(nullable=True)
    timezone: Mapped[str] = mapped_column(String(80), default="Europe/Kyiv")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserFeatureOverride(Base):
    __tablename__ = "user_feature_overrides"
    __table_args__ = (
        UniqueConstraint("user_id", "feature_key", name="uq_user_feature_override"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feature_key: Mapped[str] = mapped_column(String(80), index=True)
    enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    limit_per_hour: Mapped[int | None] = mapped_column(nullable=True)
    allowed_start_hour: Mapped[int | None] = mapped_column(nullable=True)
    allowed_end_hour: Mapped[int | None] = mapped_column(nullable=True)
    unlimited: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FeatureUsage(Base):
    __tablename__ = "feature_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "feature_key", "bucket_start", name="uq_usage_hour_bucket"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feature_key: Mapped[str] = mapped_column(String(80), index=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    count: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CustomToolItem(Base):
    __tablename__ = "custom_tool_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    subcategory: Mapped[str] = mapped_column(String(80), default="custom")
    name: Mapped[str] = mapped_column(String(250), index=True)
    code: Mapped[str] = mapped_column(String(160), index=True)
    operation_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    iso_groups: Mapped[list[str]] = mapped_column(JSON, default=list)
    dimensions: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    compatibility: Mapped[str] = mapped_column(Text, default="")
    grade_hint: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(Text, default="Добавлено администратором")
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SavedTool(Base):
    __tablename__ = "saved_tools"
    __table_args__ = (
        UniqueConstraint("user_id", "machine_profile_id", "tool_key", name="uq_saved_tool"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    machine_profile_id: Mapped[int] = mapped_column(
        ForeignKey("machine_profiles.id", ondelete="CASCADE"), index=True
    )
    tool_key: Mapped[str] = mapped_column(String(40), index=True)
    tool_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessPlan(Base):
    __tablename__ = "process_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    machine_profile_id: Mapped[int] = mapped_column(
        ForeignKey("machine_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(250))
    material_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    operations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ClientProject(Base):
    __tablename__ = "client_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    machine_profile_id: Mapped[int] = mapped_column(
        ForeignKey("machine_profiles.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(250), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    generated: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
