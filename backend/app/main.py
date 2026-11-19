
import os
import uuid

from pathlib import Path

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from pypdf import PdfReader

from .database import Base, engine, get_db

from . import models, schemas

from .audit_engine import run_audit


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ProcureGuard AI API",
    version="1.0.0",
    description=(
        "Procurement document matching, "
        "risk findings and human review API."
    )
)


origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173"
).split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


UPLOAD_DIR = Path(
    os.getenv("UPLOAD_DIR", "uploads")
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MAX_UPLOAD = (
    int(os.getenv("MAX_UPLOAD_MB", "15"))
    * 1024 * 1024
)


ALLOWED = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt"
}


def serialize(obj):

    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "service": "ProcureGuard AI"
    }


# VENDORS

@app.get("/api/vendors")
def list_vendors(
    db: Session = Depends(get_db)
):

    return [
        serialize(x)
        for x in db.query(models.Vendor)
        .order_by(models.Vendor.id.desc())
        .all()
    ]


@app.post("/api/vendors", status_code=201)
def create_vendor(
    payload: schemas.VendorCreate,
    db: Session = Depends(get_db)
):

    item = models.Vendor(
        **payload.model_dump()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return serialize(item)


# DOCUMENTS

@app.get("/api/documents")
def list_documents(
    db: Session = Depends(get_db)
):

    return [
        serialize(x)
        for x in db.query(models.Document)
        .order_by(models.Document.id.desc())
        .all()
    ]


@app.post("/api/documents", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "other",
    db: Session = Depends(get_db)
):

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in ALLOWED:

        raise HTTPException(
            400,
            "Unsupported file type. Upload PDF, PNG, JPG, JPEG or TXT."
        )

    content = await file.read()

    if len(content) > MAX_UPLOAD:

        raise HTTPException(
            413,
            "File exceeds configured upload limit."
        )

    safe_name = (
        f"{uuid.uuid4().hex}{suffix}"
    )

    path = UPLOAD_DIR / safe_name

    path.write_bytes(content)

    extracted = ""

    if suffix == ".txt":

        extracted = content.decode(
            "utf-8",
            errors="replace"
        )

    elif suffix == ".pdf":

        try:

            reader = PdfReader(str(path))

            extracted = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except Exception:

            extracted = ""

    doc = models.Document(
        filename=file.filename or safe_name,
        document_type=document_type,
        content_type=(
            file.content_type
            or "application/octet-stream"
        ),
        storage_path=str(path),
        extracted_text=extracted,
        status=(
            "text_extracted"
            if extracted
            else "uploaded"
        )
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return serialize(doc)


# PROCUREMENT RECORDS

@app.get("/api/records/{record_type}")
def list_records(
    record_type: str,
    db: Session = Depends(get_db)
):

    mapping = {
        "purchase-orders": models.PurchaseOrder,
        "receipts": models.GoodsReceipt,
        "invoices": models.Invoice,
        "contracts": models.VendorContract
    }

    model = mapping.get(record_type)

    if not model:

        raise HTTPException(
            404,
            "Unknown record type"
        )

    return [
        serialize(x)
        for x in db.query(model).all()
    ]


def create_record(db, model, data):

    item = model(**data)

    db.add(item)

    try:

        db.commit()
        db.refresh(item)

    except Exception:

        db.rollback()

        raise HTTPException(
            400,
            "Could not create record. Check references and unique identifiers."
        )

    return serialize(item)


@app.post(
    "/api/records/purchase-orders",
    status_code=201
)
def create_po(
    payload: schemas.POCreate,
    db: Session = Depends(get_db)
):

    return create_record(
        db,
        models.PurchaseOrder,
        payload.model_dump()
    )


@app.post(
    "/api/records/receipts",
    status_code=201
)
def create_receipt(
    payload: schemas.ReceiptCreate,
    db: Session = Depends(get_db)
):

    return create_record(
        db,
        models.GoodsReceipt,
        payload.model_dump()
    )


@app.post(
    "/api/records/invoices",
    status_code=201
)
def create_invoice(
    payload: schemas.InvoiceCreate,
    db: Session = Depends(get_db)
):

    return create_record(
        db,
        models.Invoice,
        payload.model_dump()
    )


@app.post(
    "/api/records/contracts",
    status_code=201
)
def create_contract(
    payload: schemas.ContractCreate,
    db: Session = Depends(get_db)
):

    return create_record(
        db,
        models.VendorContract,
        payload.model_dump()
    )


# AUDIT ENGINE

@app.post("/api/audits/run")
def audit(
    db: Session = Depends(get_db)
):

    findings = run_audit(db)

    return {
        "created_findings": len(findings),
        "findings": [
            serialize(x)
            for x in findings
        ]
    }


@app.get("/api/audits")
def audits(
    db: Session = Depends(get_db)
):

    return [
        serialize(x)
        for x in db.query(models.Finding)
        .order_by(models.Finding.created_at.desc())
        .all()
    ]


# HUMAN REVIEW QUEUE

@app.get("/api/reviews")
def reviews(
    db: Session = Depends(get_db)
):

    return [
        serialize(x)
        for x in db.query(models.Finding)
        .filter(
            models.Finding.status == "pending_review"
        )
        .order_by(models.Finding.created_at.desc())
        .all()
    ]


@app.post("/api/reviews/{finding_id}/decision")
def decide(
    finding_id: int,
    payload: schemas.DecisionCreate,
    db: Session = Depends(get_db)
):

    if payload.decision not in {
        "approved",
        "rejected",
        "needs_changes"
    }:

        raise HTTPException(
            400,
            "Decision must be approved, rejected or needs_changes."
        )

    finding = db.get(
        models.Finding,
        finding_id
    )

    if not finding:

        raise HTTPException(
            404,
            "Finding not found"
        )

    finding.status = payload.decision

    db.add(
        models.AuditEvent(
            finding_id=finding.id,
            action=payload.decision,
            actor=payload.reviewer,
            details=payload.comment
        )
    )

    db.commit()
    db.refresh(finding)

    return serialize(finding)


# AUDIT TRAIL

@app.get("/api/audit-trail")
def audit_trail(
    db: Session = Depends(get_db)
):

    return [
        serialize(x)
        for x in db.query(models.AuditEvent)
        .order_by(models.AuditEvent.created_at.desc())
        .all()
    ]


# DASHBOARD

@app.get("/api/dashboard")
def dashboard(
    db: Session = Depends(get_db)
):

    return {

        "vendors": db.query(
            models.Vendor
        ).count(),

        "documents": db.query(
            models.Document
        ).count(),

        "purchase_orders": db.query(
            models.PurchaseOrder
        ).count(),

        "invoices": db.query(
            models.Invoice
        ).count(),

        "open_findings": db.query(
            models.Finding
        ).filter_by(
            status="pending_review"
        ).count(),

        "high_risk": db.query(
            models.Finding
        ).filter_by(
            severity="high"
        ).count()

    }
