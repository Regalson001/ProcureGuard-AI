
from collections import defaultdict

from sqlalchemy.orm import Session

from . import models


PRICE_TOLERANCE = 0.02
SPLIT_REVIEW_THRESHOLD = 5000.0


def run_audit(db: Session):

    created = []

    invoices = db.query(models.Invoice).all()

    pos = {
        p.po_number: p
        for p in db.query(models.PurchaseOrder).all()
    }

    receipts = {
        r.po_number: r
        for r in db.query(models.GoodsReceipt).all()
    }

    contracts = (
        db.query(models.VendorContract)
        .filter_by(active=True)
        .all()
    )

    contract_map = {
        (c.vendor_id, c.item_description.lower()): c
        for c in contracts
    }

    def add(
        title,
        category,
        severity,
        explanation,
        invoice=None,
        vendor_id=None
    ):

        finding = models.Finding(
            title=title,
            category=category,
            severity=severity,
            explanation=explanation,
            invoice_id=invoice.id if invoice else None,
            vendor_id=vendor_id or (
                invoice.vendor_id if invoice else None
            )
        )

        db.add(finding)
        db.flush()

        db.add(
            models.AuditEvent(
                finding_id=finding.id,
                action="finding_created",
                details=explanation
            )
        )

        created.append(finding)

    seen = set()

    by_vendor_date = defaultdict(list)

    for inv in invoices:

        key = (
            inv.vendor_id,
            inv.invoice_number.strip().lower()
        )

        if key in seen:

            add(
                "Potential duplicate invoice",
                "duplicate_invoice",
                "high",
                f"Vendor {inv.vendor_id} has more than one record "
                f"with invoice number {inv.invoice_number}.",
                inv
            )

        seen.add(key)

        by_vendor_date[
            (inv.vendor_id, inv.invoice_date)
        ].append(inv)

        po = pos.get(inv.po_number)

        receipt = receipts.get(inv.po_number)

        if not po:

            add(
                "Purchase order not found",
                "missing_purchase_order",
                "high",
                f"No purchase order with reference "
                f"{inv.po_number} was found.",
                inv
            )

            continue

        if po.vendor_id != inv.vendor_id:

            add(
                "Vendor mismatch",
                "vendor_mismatch",
                "high",
                "The invoice vendor does not match the vendor "
                "recorded on the purchase order.",
                inv
            )

        if not receipt:

            add(
                "Goods receipt missing",
                "missing_receipt",
                "medium",
                f"No goods-received note is linked to "
                f"purchase order {inv.po_number}.",
                inv
            )

        else:

            if inv.quantity > receipt.quantity_received:

                add(
                    "Invoice quantity exceeds received quantity",
                    "quantity_mismatch",
                    "high",
                    f"Invoiced {inv.quantity:g} units but only "
                    f"{receipt.quantity_received:g} units were "
                    f"recorded as received.",
                    inv
                )

        if abs(inv.quantity - po.quantity) > 0.0001:

            add(
                "Invoice quantity differs from purchase order",
                "po_quantity_mismatch",
                "medium",
                f"Purchase order quantity is {po.quantity:g}; "
                f"invoice quantity is {inv.quantity:g}.",
                inv
            )

        contract = contract_map.get(
            (
                inv.vendor_id,
                po.item_description.lower()
            )
        )

        if contract:

            if inv.unit_price > (
                contract.contracted_unit_price *
                (1 + PRICE_TOLERANCE)
            ):

                add(
                    "Contract price exceeded",
                    "contract_price",
                    "high",
                    f"Invoice unit price {inv.unit_price:.2f} "
                    f"exceeds contracted price "
                    f"{contract.contracted_unit_price:.2f} "
                    f"by more than {PRICE_TOLERANCE:.0%}.",
                    inv
                )

        calculated = inv.quantity * inv.unit_price

        if abs(calculated - inv.total_amount) > max(
            0.02,
            calculated * 0.001
        ):

            add(
                "Invoice total calculation mismatch",
                "calculation_mismatch",
                "medium",
                f"Quantity × unit price equals "
                f"{calculated:.2f}, but invoice total is "
                f"{inv.total_amount:.2f}.",
                inv
            )

    for (vendor_id, invoice_date), group in by_vendor_date.items():

        if len(group) >= 2:

            total = sum(
                invoice.total_amount
                for invoice in group
            )

            if total > SPLIT_REVIEW_THRESHOLD:

                add(
                    "Possible split-invoice pattern",
                    "split_invoice",
                    "medium",
                    f"{len(group)} invoices from vendor "
                    f"{vendor_id} on {invoice_date} total "
                    f"{total:.2f}, above the "
                    f"{SPLIT_REVIEW_THRESHOLD:.2f} review threshold.",
                    vendor_id=vendor_id
                )

    db.commit()

    return created
