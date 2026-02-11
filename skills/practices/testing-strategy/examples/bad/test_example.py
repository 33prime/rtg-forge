"""BAD test example — tests implementation, no fixtures, no assertions on behavior."""


def test_everything():
    """One massive test that does too much and tests internals."""
    # No fixtures — manual setup
    service = InvoiceService(repo=FakeRepo(), notifier=FakeNotifier())

    # Tests internal method directly (implementation detail)
    assert service._generate_id() is not None

    # No specific assertion — just "doesn't crash"
    result = service.create_invoice({"items": [{"qty": 1, "price": 10}]})

    # Vague assertion
    assert result is not None

    # No error case testing
    # No edge case testing
    # No cleanup
