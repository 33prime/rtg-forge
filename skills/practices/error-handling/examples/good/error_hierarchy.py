"""Good error handling — typed hierarchy with context."""

from uuid import UUID


class DomainError(Exception):
    """Base for all domain errors."""


class NotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: UUID) -> None:
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id} not found")


class ConflictError(DomainError):
    def __init__(self, message: str, entity_id: UUID) -> None:
        self.entity_id = entity_id
        super().__init__(message)


class ValidationError(DomainError):
    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"Validation failed on '{field}': {reason}")


# Usage — catch specifically, include context
async def get_invoice(invoice_id: UUID) -> dict:
    try:
        result = await repo.get(invoice_id)
    except ConnectionError:
        raise DomainError("Database unavailable") from None

    if result is None:
        raise NotFoundError("Invoice", invoice_id)

    return result
