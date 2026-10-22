"""
ReconcileOps Engine - Financial Reconciliation System
Built with FastAPI, Pandas, and Decimal Precision
"""

import logging
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Dict, List, Optional
from enum import Enum

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, status
from pydantic import BaseModel

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ReconcileOps")

app = FastAPI(
    title="ReconcileOps Engine",
    version="2.0.0",
    description="Financial Reconciliation Microservice for CSV Invoices",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Constants & Guardrails
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".csv"}
REQUIRED_COLUMNS = {"po_number", "amount"}

# Enum Status Definitions
class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    MISMATCH_AMOUNT = "MISMATCH_AMOUNT"
    PO_NOT_FOUND = "PO_NOT_FOUND"
    INVALID_PO_NUMBER = "INVALID_PO_NUMBER"
    INVALID_AMOUNT = "INVALID_AMOUNT"

# Ledger Database Mock
MOCK_LEDGER_DB: Dict[str, Decimal] = {
    "PO-1001": Decimal("5000.00"),
    "PO-1002": Decimal("1250.00"),
    "PO-1003": Decimal("3400.00"),
}

# Pydantic Schemas
class AuditRecord(BaseModel):
    row: int
    po_number: Optional[str]
    invoice_amount: Optional[str]
    expected_amount: Optional[str]
    status: ReconciliationStatus
    message: str

class ReconciliationResponse(BaseModel):
    filename: str
    total_records: int
    summary: Dict[str, int]
    reconciliation_results: List[AuditRecord]

def validate_csv_payload(file: UploadFile) -> None:
    """Dependency for File Extension Validation"""
    if not file.filename or not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files are allowed."
        )

@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
def health_check():
    """Liveness & Readiness Probe Endpoint"""
    return {"status": "HEALTHY", "service": "ReconcileOps Engine", "version": "2.0.0"}

@app.post(
    "/api/v1/reconcile", 
    response_model=ReconciliationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Core Reconciliation"]
)
async def reconcile_invoices(file: UploadFile = File(...), _: None = Depends(validate_csv_payload)):
    """
    Processes CSV uploads, validates financial data using exact String-to-Decimal parsing,
    and audits transaction mismatches against purchase orders.
    """
    # Fix 1: Read content and check size immediately
    content = await file.read()
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty payload submitted."
        )
        
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File payload exceeds maximum limit of {MAX_FILE_SIZE_MB}MB."
        )

    # Fix 2: Read BOTH columns as 'string' to preserve exact Decimal representation
    try:
        df = pd.read_csv(
            BytesIO(content), 
            dtype={"po_number": "string", "amount": "string"}
        )
    except Exception as err:
        logger.error(f"File parsing exception: {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed CSV file structure or encoding errors."
        )

    df.columns = df.columns.str.strip().str.lower()
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Schema Validation Failed", "missing_columns": sorted(missing_cols)}
        )

    results: List[AuditRecord] = []
    
    for row_idx, row in enumerate(df.to_dict(orient="records"), start=2):
        po_id = str(row.get("po_number", "")).strip()
        raw_amt = row.get("amount")

        # PO Integrity Check
        if not po_id or po_id.lower() == "nan":
            results.append(AuditRecord(
                row=row_idx, po_number=None, invoice_amount=None, expected_amount=None,
                status=ReconciliationStatus.INVALID_PO_NUMBER, message="Null or empty Purchase Order Identifier."
            ))
            continue

        # Financial Decimal Parsing from Raw String
        try:
            if pd.isna(raw_amt) or str(raw_amt).strip().lower() == "nan":
                raise ValueError("Missing amount value")
                
            inv_amt = Decimal(str(raw_amt).strip())
            if not inv_amt.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError, TypeError):
            results.append(AuditRecord(
                row=row_idx, po_number=po_id, invoice_amount=str(raw_amt) if raw_amt else None, expected_amount=None,
                status=ReconciliationStatus.INVALID_AMOUNT, message="Invalid numerical currency format."
            ))
            continue

        # Core Reconciliation Rule Logic
        expected_amt = MOCK_LEDGER_DB.get(po_id)
        
        if expected_amt is None:
            status_res = ReconciliationStatus.PO_NOT_FOUND
            msg = "Target PO number does not exist in master ledger."
        elif expected_amt == inv_amt:
            status_res = ReconciliationStatus.MATCHED
            msg = "Invoice amount fully reconciled with Purchase Order."
        else:
            status_res = ReconciliationStatus.MISMATCH_AMOUNT
            msg = f"Discrepancy detected. Ledger expects {expected_amt}, received {inv_amt}."

        results.append(AuditRecord(
            row=row_idx,
            po_number=po_id,
            invoice_amount=str(inv_amt),
            expected_amount=str(expected_amt) if expected_amt else None,
            status=status_res,
            message=msg
        ))

    # Compute Summary Aggregation
    summary: Dict[str, int] = {}
    for res in results:
        summary[res.status.value] = summary.get(res.status.value, 0) + 1

    logger.info(f"Reconciliation completed for file '{file.filename}'. Total Records: {len(results)}")
    
    return ReconciliationResponse(
        filename=file.filename or "unknown.csv",
        total_records=len(results),
        summary=summary,
        reconciliation_results=results
    )
