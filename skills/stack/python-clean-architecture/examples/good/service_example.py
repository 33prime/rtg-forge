"""Clean service example demonstrating Python clean architecture patterns.

This service handles invoice operations with proper typing, error handling,
dependency injection, and small focused methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class InvoiceError(Exception):
    """Base error for invoice domain."""


class InvoiceNotFoundError(InvoiceError):
    def __init__(self, invoice_id: UUID) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} not found")


class InvoiceAlreadyPaidError(InvoiceError):
    def __init__(self, invoice_id: UUID) -> None:
        self.invoice_id = invoice_id
        super().__init__(f"Invoice {invoice_id} is already paid")


class InvalidLineItemError(InvoiceError):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid line item: {reason}")


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidLineItemError("Quantity must be positive")
        if self.unit_price < Decimal("0"):
            raise InvalidLineItemError("Unit price cannot be negative")

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Invoice:
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    status: InvoiceStatus
    line_items: list[LineItem]

    @property
    def subtotal(self) -> Decimal:
        return sum((item.total for item in self.line_items), Decimal("0"))


@dataclass(frozen=True)
class CreateInvoiceRequest:
    tenant_id: UUID
    customer_id: UUID
    line_items: list[LineItem]


# ---------------------------------------------------------------------------
# Protocols (dependency contracts)
# ---------------------------------------------------------------------------

from typing import Protocol


class InvoiceRepository(Protocol):
    async def get(self, invoice_id: UUID) -> Invoice | None: ...
    async def save(self, invoice: Invoice) -> None: ...
    async def list_by_tenant(
        self, tenant_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[Invoice]: ...


class NotificationService(Protocol):
    async def send_invoice_created(self, invoice: Invoice) -> None: ...
    async def send_invoice_paid(self, invoice: Invoice) -> None: ...


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class InvoiceService:
    """Handles invoice business logic.

    Dependencies are injected through the constructor. The service is stateless
    and all methods operate on explicit inputs and outputs.
    """

    def __init__(
        self,
        repo: InvoiceRepository,
        notifier: NotificationService,
    ) -> None:
        self._repo = repo
        self._notifier = notifier

    async def create_invoice(self, request: CreateInvoiceRequest) -> Invoice:
        """Create a new draft invoice from a request."""
        self._validate_line_items(request.line_items)

        invoice = Invoice(
            id=self._generate_id(),
            tenant_id=request.tenant_id,
            customer_id=request.customer_id,
            status=InvoiceStatus.DRAFT,
            line_items=request.line_items,
        )

        await self._repo.save(invoice)
        await self._notifier.send_invoice_created(invoice)
        return invoice

    async def mark_as_paid(self, invoice_id: UUID) -> Invoice:
        """Mark an existing invoice as paid."""
        invoice = await self._get_invoice_or_raise(invoice_id)

        if invoice.status == InvoiceStatus.PAID:
            raise InvoiceAlreadyPaidError(invoice_id)

        invoice.status = InvoiceStatus.PAID
        await self._repo.save(invoice)
        await self._notifier.send_invoice_paid(invoice)
        return invoice

    async def get_invoice(self, invoice_id: UUID) -> Invoice:
        """Retrieve a single invoice by ID."""
        return await self._get_invoice_or_raise(invoice_id)

    # -- Private helpers ---------------------------------------------------

    async def _get_invoice_or_raise(self, invoice_id: UUID) -> Invoice:
        invoice = await self._repo.get(invoice_id)
        if invoice is None:
            raise InvoiceNotFoundError(invoice_id)
        return invoice

    def _validate_line_items(self, items: list[LineItem]) -> None:
        if not items:
            raise InvalidLineItemError("Invoice must have at least one line item")

    @staticmethod
    def _generate_id() -> UUID:
        from uuid import uuid4
        return uuid4()
