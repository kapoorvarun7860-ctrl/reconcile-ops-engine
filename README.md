# ReconcileOps Engine

A FastAPI project that checks invoice amounts in a CSV file against purchase order amounts.

## Features

- Upload invoice data from a CSV file
- Check invoice amounts against purchase orders
- Show whether amounts match
- Open the API documentation in a browser

## Built With

- Python
- FastAPI
- Pandas
- Decimal

## How to Run

Install the required packages:

```bash
python -m pip install fastapi uvicorn pandas python-multipart
```

Start the API:

```bash
uvicorn main:app --reload
```

Open the API documentation:

http://127.0.0.1:8000/docs
