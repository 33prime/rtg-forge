"""Good test example — focused, uses fixtures, tests behavior not implementation."""

import pytest
from decimal import Decimal
from uuid import uuid4


@pytest.fixture
def invoice_service(mock_repo, mock_notifier):
    """Compose service with test doubles."""
    return InvoiceService(repo=mock_repo, notifier=mock_notifier)


@pytest.fixture
def sample_request():
    """Factory for test invoice requests."""
    return CreateInvoiceRequest(
        tenant_id=uuid4(),
        customer_id=uuid4(),
        line_items=[LineItem(description="Widget", quantity=2, unit_price=Decimal("10.00"))],
    )


class TestInvoiceCreation:
    async def test_creates_draft_invoice(self, invoice_service, sample_request):
        invoice = await invoice_service.create_invoice(sample_request)

        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.subtotal == Decimal("20.00")

    async def test_rejects_empty_line_items(self, invoice_service):
        request = CreateInvoiceRequest(
            tenant_id=uuid4(),
            customer_id=uuid4(),
            line_items=[],
        )

        with pytest.raises(InvalidLineItemError, match="at least one line item"):
            await invoice_service.create_invoice(request)
