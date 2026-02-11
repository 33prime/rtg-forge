from dataclasses import dataclass
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


module_info = ModuleInfo(
    name="stakeholder_enrichment",
    version="0.1.0",
    description="Multi-source stakeholder profile enrichment with AI synthesis",
    router=router,
    prefix="/api/v1/enrichment",
    tags=["enrichment"],
)
