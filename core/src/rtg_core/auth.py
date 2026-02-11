"""Authentication dependencies for FastAPI."""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from rtg_core.config import CoreConfig

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def _get_config() -> CoreConfig:
    return CoreConfig()


async def get_api_key(
    api_key: str | None = Security(api_key_header),
) -> str:
    """FastAPI dependency that validates an API key from the X-API-Key header."""
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    # In production, validate against stored API keys.
    # For now, accept any non-empty key.
    return api_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency that validates a Supabase JWT and returns user info."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = credentials.credentials
    try:
        from supabase import create_client

        config = _get_config()
        client = create_client(config.supabase_url, config.supabase_service_key)
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": str(user_response.user.id), "email": user_response.user.email}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}") from e
