"""
BAD: Service layer tangled with framework concerns.

Problems:
- Imports FastAPI types (HTTPException, Request, Depends)
- Raises HTTP exceptions instead of domain exceptions
- Reads config via os.getenv instead of pydantic-settings
- Uses global mutable state (_cache)
- Business logic would need refactoring before forge extraction
"""

import os
from uuid import UUID

from fastapi import HTTPException, Request, Depends  # BAD: framework import
from supabase import Client

# BAD: global mutable state
_cache: dict[str, dict] = {}


# BAD: no config class, raw os.getenv
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
TAX_RATE = float(os.getenv("TAX_RATE", "0.0"))


# BAD: function instead of class, no clear boundary
async def create_invoice(request: Request, data: dict) -> dict:
    """Create an invoice — but tied to FastAPI Request object."""
    db: Client = request.app.state.db  # BAD: reaching into app state

    invoice_number = data.get("invoice_number")  # BAD: raw dict, no model
    if not invoice_number:
        raise HTTPException(status_code=400, detail="Missing invoice number")  # BAD: HTTP in service

    # BAD: business logic mixed with HTTP error handling
    existing = db.table("invoices").select("*").eq("invoice_number", invoice_number).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Duplicate invoice")  # BAD

    total = 0
    for item in data.get("items", []):  # BAD: untyped dict access
        total += item["price"] * item["qty"]

    result = db.table("invoices").insert({
        "invoice_number": invoice_number,
        "client_name": data["client_name"],
        "total": total,
    }).execute()

    # BAD: caching in global state
    _cache[invoice_number] = result.data[0]

    return result.data[0]  # BAD: returning raw dict, no response model


async def get_invoice(request: Request, invoice_id: str) -> dict:
    # BAD: no UUID type, manual parsing
    try:
        uid = UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    # BAD: check cache first (global mutable state)
    if invoice_id in _cache:
        return _cache[invoice_id]

    db: Client = request.app.state.db
    result = db.table("invoices").select("*").eq("id", str(uid)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Not found")  # BAD: HTTP in service

    return result.data[0]
