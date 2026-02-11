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
    name="stakeholder_enrichment",
    version="1.0.0",
    description="Multi-source stakeholder enrichment pipeline with AI synthesis, ICP scoring, and project idea generation",
    router=router,
    prefix="/api/v1/enrichment",
    tags=["enrichment"],
)
