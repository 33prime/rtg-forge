"""BAD Langfuse tracing example — no decoration, no metadata, no structure."""


async def process_query(query: str, user_id: str) -> str:
    """No tracing at all — invisible to observability."""
    # No @observe() decorator
    # No user_id tracking
    # No metadata
    context = await retrieve_context(query)
    response = await generate_response(query, context)
    # No flush before returning
    return response


async def retrieve_context(query: str) -> str:
    # No tracing span — retrieval latency is invisible
    return "context"


async def generate_response(query: str, context: str) -> str:
    # No tracing span — LLM cost and latency are invisible
    return "response"
