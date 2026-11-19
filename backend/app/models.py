
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean
)

from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(200),
        index=True
    )

    tax_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    bank_account: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    address: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    filename: Mapped[str] = mapped_column(
        String(255)
    )

    document_type: Mapped[str] = mapped_column(
        String(40)
    )

    content_type: Mapped[str] = mapped_column(
        String(100)
    )

    storage_path: Mapped[str] = mapped_column(
        String(500)
    )

    extracted_text: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    po_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id")
    )

    item_description: Mapped[str] = mapped_column(
        String(300)
    )

    quantity: Mapped[float] = mapped_column(Float)

    unit_price: Mapped[float] = mapped_column(Float)

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)

    grn_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True
    )

    po_number: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    quantity_received: Mapped[float] = mapped_column(
        Float
    )

    received_date: Mapped[str] = mapped_column(
        String(20)
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)

    invoice_number: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id")
    )

    po_number: Mapped[str] = mapped_column(
        String(100),
        index=True
    )

    invoice_date: Mapped[str] = mapped_column(
        String(20)
    )

    quantity: Mapped[float] = mapped_column(Float)

    unit_price: Mapped[float] = mapped_column(Float)

    total_amount: Mapped[float] = mapped_column(Float)

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )


class VendorContract(Base):
    __tablename__ = "vendor_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)

    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id")
    )

    item_description: Mapped[str] = mapped_column(
        String(300)
    )

    contracted_unit_price: Mapped[float] = mapped_column(
        Float
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD"
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(250)
    )

    category: Mapped[str] = mapped_column(
        String(60)
    )

    severity: Mapped[str] = mapped_column(
        String(20)
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending_review"
    )

    vendor_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendors.id"),
        nullable=True
    )

    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"),
        nullable=True
    )

    explanation: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id"),
        nullable=True
    )

    action: Mapped[str] = mapped_column(
        String(80)
    )

    actor: Mapped[str] = mapped_column(
        String(120),
        default="system"
    )

    details: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc
    )
