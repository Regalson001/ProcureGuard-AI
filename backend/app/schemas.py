
from pydantic import BaseModel, Field
from typing import Optional


class VendorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    tax_id: Optional[str] = None
    bank_account: Optional[str] = None
    address: Optional[str] = None


class POCreate(BaseModel):
    po_number: str
    vendor_id: int
    item_description: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    currency: str = "USD"


class ReceiptCreate(BaseModel):
    grn_number: str
    po_number: str
    quantity_received: float = Field(gt=0)
    received_date: str


class InvoiceCreate(BaseModel):
    invoice_number: str
    vendor_id: int
    po_number: str
    invoice_date: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    total_amount: float = Field(ge=0)
    currency: str = "USD"


class ContractCreate(BaseModel):
    vendor_id: int
    item_description: str
    contracted_unit_price: float = Field(ge=0)
    currency: str = "USD"
    active: bool = True


class DecisionCreate(BaseModel):
    decision: str
    reviewer: str = "reviewer"
    comment: str = ""
