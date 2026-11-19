
from app.database import Base, engine, SessionLocal

from app import models


Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:

    existing = (
        db.query(models.Vendor)
        .filter_by(
            name="Northstar Office Supplies"
        )
        .first()
    )

    if existing:

        print("Demo data already exists.")

    else:

        vendor = models.Vendor(
            name="Northstar Office Supplies",
            tax_id="DEMO-TAX-001",
            bank_account="DEMO-ACCOUNT-001",
            address="Nairobi, Kenya"
        )

        db.add(vendor)
        db.flush()

        db.add(
            models.PurchaseOrder(
                po_number="PO-DEMO-1001",
                vendor_id=vendor.id,
                item_description="A4 Copy Paper",
                quantity=100,
                unit_price=5.00,
                currency="USD"
            )
        )

        db.add(
            models.GoodsReceipt(
                grn_number="GRN-DEMO-1001",
                po_number="PO-DEMO-1001",
                quantity_received=90,
                received_date="2026-11-18"
            )
        )

        db.add(
            models.VendorContract(
                vendor_id=vendor.id,
                item_description="A4 Copy Paper",
                contracted_unit_price=5.00,
                currency="USD",
                active=True
            )
        )

        db.add(
            models.Invoice(
                invoice_number="INV-DEMO-9001",
                vendor_id=vendor.id,
                po_number="PO-DEMO-1001",
                invoice_date="2026-11-19",
                quantity=100,
                unit_price=5.75,
                total_amount=575.00,
                currency="USD"
            )
        )

        db.commit()

        print(
            "Demo data created. Run POST /api/audits/run "
            "to generate findings."
        )

finally:

    db.close()
