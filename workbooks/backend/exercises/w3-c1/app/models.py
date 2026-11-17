from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str | None] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("tenant_id", "email"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    email: Mapped[str] = mapped_column(String(320))
    full_name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IdempotencyKey(Base):
    """One row per (tenant, Idempotency-Key). The composite primary key is the uniqueness claim."""

    __tablename__ = "idempotency_keys"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16))  # in_progress | completed
    response_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
