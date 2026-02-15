from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import APIRouter

from .router import router


@dataclass
class ModuleInfo:
    name: str
    version: str
    description: str
    router: APIRouter
    prefix: str
    tags: list[str]
    on_startup: Optional[Callable] = None
    on_shutdown: Optional[Callable] = None


module_info = ModuleInfo(
    name="call_intelligence",
    version="0.1.0",
    description="Meeting recording, transcription, and AI-powered multi-dimensional call analysis",
    router=router,
    prefix="/api/v1/call-intelligence",
    tags=["call-intelligence"],
)
