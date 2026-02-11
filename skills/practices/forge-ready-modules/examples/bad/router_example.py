"""
BAD: Fat router with business logic embedded in route handlers.

Problems:
- Database queries directly in routes
- No service layer — logic is not extractable
- Raw dict responses instead of Pydantic models
- No dependency injection
- Error handling mixed into business logic
- Impossible to extract to forge without rewriting
"""

import os
from fastapi import APIRouter, Request
from supabase import create_client

router = APIRouter()

# BAD: client created at module level with raw env vars
db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


@router.post("/")
async def create_invoice(request: Request):
    # BAD: manual JSON parsing instead of Pydantic model
    data = await request.json()

    invoice_number = data.get("invoice_number", "")
    if not invoice_number:
        return {"error": "Missing invoice number"}  # BAD: no HTTP status code

    # BAD: database query in route handler
    existing = db.table("invoices").select("*").eq(
        "invoice_number", invoice_number
    ).execute()

    if existing.data:
        return {"error": "Duplicate"}  # BAD: 200 status with error body

    # BAD: business logic (total calculation) in route
    total = 0
    for item in data.get("items", []):
        total += item["price"] * item["qty"]  # BAD: untyped dict access

    # BAD: direct insert in route
    result = db.table("invoices").insert({
        "invoice_number": invoice_number,
        "client_name": data["client_name"],
        "total": total,
    }).execute()

    return result.data[0]  # BAD: raw dict, no response model


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):  # BAD: str instead of UUID
    # BAD: database query in route
    result = db.table("invoices").select("*").eq("id", invoice_id).execute()

    if not result.data:
        return {"error": "Not found"}  # BAD: 200 with error

    return result.data[0]  # BAD: raw dict
