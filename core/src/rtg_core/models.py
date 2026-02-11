"""Base models with common configuration."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with camelCase alias generation and from_attributes support."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampMixin(BaseModel):
    """Mixin that adds created_at and updated_at timestamps."""

    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectMixin(BaseModel):
    """Mixin that adds project_id for multi-tenant isolation."""

    project_id: UUID
