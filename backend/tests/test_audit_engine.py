
from app.database import Base, engine, SessionLocal

from app import models

from app.audit_engine import run_audit


def test_contract_price_violation_creates_finding():

    Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    vendor = models.Vendor(
        name="Test Supplier"
    )

    db.add(vendor)

    db.commit()

    db.refresh(vendor)

    db.add(
        models.PurchaseOrder(
            po_number="PO-1",
            vendor_id=vendor.id,
            item_description="Paper",
            quantity=10,
            unit_price=10,
            currency="USD"
        )
    )

    db.add(
        models.GoodsReceipt(
            grn_number="GRN-1",
            po_number="PO-1",
            quantity_received=10,
            received_date="2026-01-01"
        )
    )

    db.add(
        models.VendorContract(
            vendor_id=vendor.id,
            item_description="Paper",
            contracted_unit_price=10,
            currency="USD",
            active=True
        )
    )

    db.add(
        models.Invoice(
            invoice_number="INV-1",
            vendor_id=vendor.id,
            po_number="PO-1",
            invoice_date="2026-01-02",
            quantity=10,
            unit_price=12,
            total_amount=120,
            currency="USD"
        )
    )

    db.commit()

    findings = run_audit(db)

    assert any(
        finding.category == "contract_price"
        for finding in findings
    )

    db.close()
