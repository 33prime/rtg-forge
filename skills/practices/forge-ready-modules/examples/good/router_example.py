"""
GOOD: Thin router that delegates everything to the service layer.

This router:
- Validates input via Pydantic models (automatic)
- Calls the service for all logic
- Converts domain exceptions to HTTP responses
- Returns typed response models
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from .models import (
    CreateInvoiceRequest,
    InvoiceResponse,
    InvoiceListResponse,
)
from .service import InvoiceService

router = APIRouter()


def get_service() -> InvoiceService:
    return InvoiceService()


@router.post(
    "/",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_invoice(
    body: CreateInvoiceRequest,
    service: InvoiceService = Depends(get_service),
) -> InvoiceResponse:
    try:
        invoice = await service.create(body)
        return InvoiceResponse.from_domain(invoice)
    except service.DuplicateInvoiceError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_service),
) -> InvoiceResponse:
    try:
        invoice = await service.get(invoice_id)
        return InvoiceResponse.from_domain(invoice)
    except service.InvoiceNotFoundError:
        raise HTTPException(status_code=404, detail="Invoice not found")


@router.get("/", response_model=InvoiceListResponse)
async def list_invoices(
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    service: InvoiceService = Depends(get_service),
) -> InvoiceListResponse:
    items, total = await service.list(
        limit=limit, offset=offset, status=status_filter
    )
    return InvoiceListResponse(
        items=[InvoiceResponse.from_domain(i) for i in items],
        total=total,
    )
