"""Good API design — consistent resource naming, status codes, error shape, pagination."""

from fastapi import APIRouter, Query, status
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/v1/invoices", tags=["invoices"])


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


@router.get("", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
async def list_invoices(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """GET /v1/invoices — list with pagination."""
    ...


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_invoice(request: CreateInvoiceRequest):
    """POST /v1/invoices — create, returns 201."""
    ...


@router.get("/{invoice_id}", status_code=status.HTTP_200_OK)
async def get_invoice(invoice_id: UUID):
    """GET /v1/invoices/:id — single resource, 404 if missing."""
    ...


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(invoice_id: UUID):
    """DELETE /v1/invoices/:id — 204 on success."""
    ...
