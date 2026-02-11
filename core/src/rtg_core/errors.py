"""Forge error hierarchy and FastAPI exception handler."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel as PydanticBaseModel


class ForgeError(Exception):
    """Base exception for all Forge errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(ForgeError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(ForgeError):
    """Validation failed."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)


class ConfigError(ForgeError):
    """Configuration error."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=500)


class ErrorResponse(PydanticBaseModel):
    """Standard error response model."""

    error: str
    detail: str
    status_code: int


def register_exception_handlers(app: FastAPI) -> None:
    """Register Forge exception handlers on a FastAPI app."""

    @app.exception_handler(ForgeError)
    async def forge_error_handler(_request: Request, exc: ForgeError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": type(exc).__name__, "detail": exc.message, "status_code": exc.status_code},
        )
