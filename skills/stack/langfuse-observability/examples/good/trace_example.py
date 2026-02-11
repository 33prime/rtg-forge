"""Good Langfuse tracing example — proper decoration, span nesting, metadata."""

from langfuse.decorators import langfuse_context, observe


@observe()
async def process_query(query: str, user_id: str) -> str:
    """Top-level trace with user metadata."""
    langfuse_context.update_current_trace(
        user_id=user_id,
        metadata={"source": "api"},
    )

    context = await retrieve_context(query)
    response = await generate_response(query, context)
    return response


@observe()
async def retrieve_context(query: str) -> str:
    """Nested span for retrieval step."""
    langfuse_context.update_current_observation(
        metadata={"retriever": "vector_store"},
    )
    # ... retrieval logic
    return "retrieved context"


@observe()
async def generate_response(query: str, context: str) -> str:
    """Nested span for generation step."""
    # ... generation logic
    langfuse_context.update_current_observation(
        metadata={"model": "claude-3-5-sonnet", "temperature": 0.0},
    )
    return "generated response"
