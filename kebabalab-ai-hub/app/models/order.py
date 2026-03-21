import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number: Mapped[int] = mapped_column(Integer, autoincrement=True, unique=True, index=True)

    # Customer
    customer_phone: Mapped[str] = mapped_column(String(20), index=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    channel: Mapped[str] = mapped_column(String(20), default="voice")  # voice, whatsapp, sms, web

    # Order details
    items: Mapped[dict] = mapped_column(JSON)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    gst: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default="confirmed",
        index=True,
    )  # confirmed, preparing, ready, completed, cancelled

    # Timing
    pickup_time: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    estimated_ready: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_phone": self.customer_phone,
            "customer_name": self.customer_name,
            "channel": self.channel,
            "items": self.items,
            "subtotal": float(self.subtotal),
            "gst": float(self.gst),
            "total": float(self.total),
            "status": self.status,
            "pickup_time": self.pickup_time,
            "estimated_ready": self.estimated_ready,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
