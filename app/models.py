from __future__ import annotations

from datetime import datetime

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
