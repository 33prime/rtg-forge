"""
GOOD: Service layer with zero framework imports.

This service can be:
- Extracted to RTG Forge as-is
- Unit tested without spinning up FastAPI
- Imported in a CLI, script, or different framework
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .config import InvoiceConfig
from .models import CreateInvoiceRequest, Invoice, LineItem


# --- Domain exceptions (defined here, not in router) ---

class InvoiceError(Exception):
    """Base error for invoice domain."""


class DuplicateInvoiceError(InvoiceError):
    def __init__(self, invoice_number: str) -> None:
        self.invoice_number = invoice_number
        super().__init__(f"Invoice {invoice_number} already exists")


class InvoiceNotFoundError(InvoiceError):
    def __init__(self, invoice_id: UUID) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} not found")


class InvoiceService:
    """Invoice business logic. No FastAPI, no HTTP, no framework coupling."""

    # Attach exceptions so callers can reference them via the service instance
    DuplicateInvoiceError = DuplicateInvoiceError
    InvoiceNotFoundError = InvoiceNotFoundError

    def __init__(self) -> None:
        self.config = InvoiceConfig()

    async def create(self, request: CreateInvoiceRequest) -> Invoice:
        """Create a new invoice. Raises DuplicateInvoiceError if number exists."""
        existing = await self._find_by_number(request.invoice_number)
        if existing:
            raise DuplicateInvoiceError(request.invoice_number)

        total = sum(
            item.unit_price * item.quantity for item in request.line_items
        )

        # Database insert via Supabase client
        result = await self._insert(
            invoice_number=request.invoice_number,
            client_name=request.client_name,
            total=total,
        )

        return Invoice(**result)

    async def get(self, invoice_id: UUID) -> Invoice:
        """Get an invoice by ID. Raises InvoiceNotFoundError if missing."""
        result = await self._find_by_id(invoice_id)
        if not result:
            raise InvoiceNotFoundError(invoice_id)
        return Invoice(**result)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[list[Invoice], int]:
        """List invoices with pagination and optional status filter."""
        # ... database query with filters
        ...

    # --- Private helpers ---

    async def _find_by_id(self, invoice_id: UUID) -> dict | None:
        ...

    async def _find_by_number(self, invoice_number: str) -> dict | None:
        ...

    async def _insert(self, **kwargs) -> dict:
        ...
