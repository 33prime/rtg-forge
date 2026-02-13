"""ICP Signal Extraction module — extract, route, cluster, and review ICP signals."""

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
    name="icp_signal_extraction",
    version="0.1.0",
    description="Extract, route, cluster, and review ICP signals from call transcripts and beta applications using LangGraph",
    router=router,
    prefix="/api/v1/icp",
    tags=["icp-intelligence"],
)
