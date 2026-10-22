# ReconcileOps Engine 🚀

An enterprise-grade microservice for automated financial reconciliation between vendor invoice CSV streams and corporate Purchase Order (PO) master ledgers, built with Python, FastAPI, Pandas, and Decimal precision.

## 🌟 Key Technical Highlights
- **Arbitrary-Precision Financial Computations:** Uses Python's `Decimal` type to prevent rounding errors in high-value currency audits.
- **Strict Data Validation & Schema Guards:** Validates payloads, file extensions, and schema columns using Pydantic v2 and custom FastAPI dependencies.
- **Production-Ready Operations:** Includes liveness/readiness `/health` probes, structured JSON logging, and dynamic OpenAPI (Swagger/ReDoc) documentation.

## 🛠 Tech Stack
- **Backend Framework:** FastAPI (Python 3.10+)
- **Data Engineering:** Pandas, BytesIO
- **Validation & Typing:** Pydantic, Python Decimal, Enum

## 🚀 Quickstart Guide

1. Clone repository & install dependencies:
```bash
git clone [https://github.com/kapoorvarun7860-ctrl/reconcile-ops-engine.git](https://github.com/kapoorvarun7860-ctrl/reconcile-ops-engine.git)
cd reconcile-ops-engine
pip install -r requirements.txt

uvicorn main:app --reload
