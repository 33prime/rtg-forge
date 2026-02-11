"""BAD parallel execution — sequential when parallel is possible, no error handling."""

import asyncio


async def process_invoices(invoice_ids: list[str]) -> list[dict]:
    """Processes invoices one at a time — wastes time."""
    results = []
    for invoice_id in invoice_ids:
        # BAD: Sequential execution of independent tasks
        result = await invoice_service.process(invoice_id)
        results.append(result)
    # If each takes 1s and there are 100 invoices, this takes 100s instead of ~10s
    return results
