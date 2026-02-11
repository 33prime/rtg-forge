"""Good parallel execution — gather with error handling, bounded concurrency."""

import asyncio


async def process_invoices(invoice_ids: list[str]) -> list[dict]:
    """Process multiple invoices in parallel with bounded concurrency."""
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

    async def process_one(invoice_id: str) -> dict:
        async with semaphore:
            return await invoice_service.process(invoice_id)

    results = await asyncio.gather(
        *(process_one(id) for id in invoice_ids),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    if failures:
        logger.warning(f"{len(failures)} invoices failed processing")

    return successes
