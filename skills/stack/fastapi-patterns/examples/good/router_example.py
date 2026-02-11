"""Clean FastAPI router demonstrating proper patterns.

- Async route handlers
- Depends() for dependency injection
- Pydantic request/response models
- Correct HTTP status codes
- Thin handlers that delegate to services
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Pydantic models — request and response are SEPARATE
# ---------------------------------------------------------------------------

class LineItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    quantity: int = Field(gt=0, le=10_000)
    unit_price: Decimal = Field(ge=0, decimal_places=2)

    model_config = ConfigDict(strict=True)


class CreateInvoiceRequest(BaseModel):
    customer_id: UUID
    line_items: list[LineItemRequest] = Field(min_length=1, max_length=100)

    model_config = ConfigDict(strict=True)


class LineItemResponse(BaseModel):
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal


class InvoiceResponse(BaseModel):
    id: UUID
    customer_id: UUID
    status: str
    subtotal: Decimal
    line_items: list[LineItemResponse]


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Dependencies — defined as functions, composed with Depends()
# ---------------------------------------------------------------------------

async def get_current_user(
    # In reality, this would parse a JWT token
) -> dict:
    """Authenticate the current user from the request token."""
    return {"user_id": "...", "tenant_id": "..."}


async def get_invoice_service(
    # In reality, would depend on get_db_session, etc.
) -> object:
    """Build and return the invoice service with all dependencies."""
    ...


# ---------------------------------------------------------------------------
# Router — thin handlers, correct status codes
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    service: Annotated[object, Depends(get_invoice_service)],
    user: Annotated[dict, Depends(get_current_user)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> InvoiceListResponse:
    """List invoices for the current user's tenant."""
    invoices = await service.list_invoices(  # type: ignore[attr-defined]
        tenant_id=user["tenant_id"],
        limit=limit,
        offset=offset,
    )
    return InvoiceListResponse(
        items=[_to_response(inv) for inv in invoices.items],
        total=invoices.total,
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=InvoiceResponse)
async def create_invoice(
    request: CreateInvoiceRequest,
    service: Annotated[object, Depends(get_invoice_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> InvoiceResponse:
    """Create a new draft invoice."""
    invoice = await service.create_invoice(request, tenant_id=user["tenant_id"])  # type: ignore[attr-defined]
    return _to_response(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: Annotated[object, Depends(get_invoice_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> InvoiceResponse:
    """Get a single invoice by ID."""
    invoice = await service.get_invoice(invoice_id)  # type: ignore[attr-defined]
    return _to_response(invoice)


@router.post("/{invoice_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def send_invoice(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
    service: Annotated[object, Depends(get_invoice_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> dict[str, str]:
    """Queue an invoice for sending. Returns immediately."""
    invoice = await service.get_invoice(invoice_id)  # type: ignore[attr-defined]
    background_tasks.add_task(service.send_invoice_email, invoice)  # type: ignore[attr-defined]
    return {"status": "accepted", "message": "Invoice is being sent"}


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    service: Annotated[object, Depends(get_invoice_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """Delete a draft invoice."""
    await service.delete_invoice(invoice_id)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _to_response(invoice: object) -> InvoiceResponse:
    """Convert a domain Invoice to an API InvoiceResponse."""
    # In real code, invoice would be a typed domain object
    return InvoiceResponse(
        id=invoice.id,  # type: ignore[attr-defined]
        customer_id=invoice.customer_id,  # type: ignore[attr-defined]
        status=invoice.status.value,  # type: ignore[attr-defined]
        subtotal=invoice.subtotal,  # type: ignore[attr-defined]
        line_items=[
            LineItemResponse(
                description=li.description,
                quantity=li.quantity,
                unit_price=li.unit_price,
                total=li.total,
            )
            for li in invoice.line_items  # type: ignore[attr-defined]
        ],
    )
