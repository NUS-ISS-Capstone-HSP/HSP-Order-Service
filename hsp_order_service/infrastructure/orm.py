from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from hsp_order_service.infrastructure.db import Base


class EchoRecordORM(Base):
    __tablename__ = "echo_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message: Mapped[str] = mapped_column(Text(), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


class OrderORM(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_status", "status"),
        Index("ix_orders_service_type", "service_type"),
        Index("ix_orders_created_at", "created_at"),
    )

    order_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    service_address: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[str] = mapped_column(String(32), nullable=False)
    appointment_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
