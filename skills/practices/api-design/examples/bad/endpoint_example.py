"""BAD API design — verbs in URLs, wrong status codes, inconsistent errors."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/getInvoices")  # Verb in URL, should be GET /invoices
def get_invoices():
    return {"invoices": [...]}  # No pagination, raw list


@router.post("/createInvoice")  # Verb in URL, no 201 status
def create_invoice(data: dict):
    return {"success": True}  # No resource in response


@router.get("/deleteInvoice/{id}")  # GET for deletion!
def delete_invoice(id):
    return {"deleted": True}  # Returns 200 instead of 204


@router.post("/invoice/update")  # Not RESTful at all
def update_invoice(data: dict):
    if not data.get("id"):
        return {"error": True}  # Inconsistent error shape, returns 200
    return {"ok": 1}  # Different success shape from other endpoints
