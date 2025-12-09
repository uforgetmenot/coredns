"""Schemas for Corefile backup APIs"""

from typing import List

from pydantic import BaseModel


class BackupInfo(BaseModel):
    id: str
    filename: str
    size: int
    created_at: str
    is_latest: bool = False
    content: str | None = None


class BackupListData(BaseModel):
    backups: List[BackupInfo]
    total: int
    page: int
    page_size: int


class BackupListResponse(BaseModel):
    success: bool = True
    data: BackupListData


class BackupDetailResponse(BaseModel):
    success: bool = True
    data: BackupInfo


class RestoreResponse(BaseModel):
    success: bool = True
    data: dict
    message: str


class DeleteBackupResponse(BaseModel):
    success: bool = True
    message: str
