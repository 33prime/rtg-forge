"""Pydantic models for the codebase analyzer module."""

from pydantic import BaseModel


class ContextResponse(BaseModel):
    """Response for GET /codebase-context — returns the current context document."""

    content: str
    generated_at: str
    status: str


class RefreshResponse(BaseModel):
    """Response for POST /codebase-context/refresh — confirms background task started."""

    status: str = "accepted"
    message: str = "Codebase context refresh started. Incremental updates take ~10s, full analysis ~30s."
