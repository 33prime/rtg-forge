from dataclasses import dataclass, field
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
    name="codebase_analyzer",
    version="1.0.0",
    description="GitHub-powered codebase analysis with Claude synthesis for AI instruction generation",
    router=router,
    prefix="/api/v1/codebase-context",
    tags=["codebase-context"],
)
