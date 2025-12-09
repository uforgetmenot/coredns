"""Schemas for Corefile API"""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel, ConfigDict


class CorefileStats(BaseModel):
    total_zones: int
    total_records: int
    active_records: int


class CorefileData(BaseModel):
    content: str
    stats: CorefileStats
    generated_at: datetime
    corefile_path: str | None = None


class CorefileGenerateResponse(BaseModel):
    success: bool = True
    data: CorefileData
    message: str


class CorefilePreviewResponse(BaseModel):
    success: bool = True
    data: CorefileData
