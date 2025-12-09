"""Schemas for CoreDNS reload/status endpoints"""

from typing import Any, Dict

from pydantic import BaseModel


class CoreDNSReloadResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    message: str


class CoreDNSStatusResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
