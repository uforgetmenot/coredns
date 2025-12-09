"""
DNS Record Pydantic schemas for API request/response
"""

from datetime import datetime
from typing import Dict, List, Optional
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_RECORD_TYPES = ["A", "AAAA", "CNAME"]
ALLOWED_STATUSES = ["active", "inactive", "deleted"]


def _validate_ip(value: str) -> str:
    pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if not re.match(pattern, value):
        raise ValueError("Invalid IPv4 address format")

    parts = value.split(".")
    if not all(0 <= int(part) <= 255 for part in parts):
        raise ValueError("IPv4 address parts must be between 0 and 255")

    return value


def _validate_hostname(value: str) -> str:
    pattern = r"^[a-zA-Z0-9-]+$"
    if not re.match(pattern, value):
        raise ValueError("Hostname can only contain letters, numbers, and hyphens")
    return value


def _validate_record_type(value: str) -> str:
    if value not in ALLOWED_RECORD_TYPES:
        raise ValueError(f"Record type must be one of: {', '.join(ALLOWED_RECORD_TYPES)}")
    return value


def _validate_status(value: str) -> str:
    if value not in ALLOWED_STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(ALLOWED_STATUSES)}")
    return value


class DNSRecordCreate(BaseModel):
    """请求模型：创建 DNS 记录"""

    zone: str = Field(..., min_length=1, max_length=255, description="DNS Zone")
    hostname: str = Field(..., min_length=1, max_length=255, description="主机名")
    ip_address: str = Field(..., description="IP 地址")
    record_type: str = Field("A", description="记录类型 (A/AAAA/CNAME)")
    description: Optional[str] = Field(None, max_length=500, description="记录描述")
    status: str = Field("active", description="状态 (active/inactive)")

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        """验证 IPv4 地址格式"""

        return _validate_ip(value)

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        return _validate_hostname(value)

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, value: str) -> str:
        return _validate_record_type(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return _validate_status(value)


class DNSRecordUpdate(BaseModel):
    """完整更新模型 (PUT)"""

    zone: str = Field(..., min_length=1, max_length=255, description="DNS Zone")
    hostname: str = Field(..., min_length=1, max_length=255, description="主机名")
    ip_address: str = Field(..., description="IP 地址")
    record_type: str = Field("A", description="记录类型")
    description: Optional[str] = Field(None, max_length=500, description="记录描述")
    status: str = Field("active", description="状态")

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        return _validate_ip(value)

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        return _validate_hostname(value)

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, value: str) -> str:
        return _validate_record_type(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        return _validate_status(value)


class DNSRecordPatch(BaseModel):
    """部分更新模型 (PATCH)"""

    zone: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    ip_address: Optional[str] = None
    record_type: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_ip(value)

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_hostname(value)

    @field_validator("record_type")
    @classmethod
    def validate_record_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_record_type(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_status(value)


class DNSRecordResponse(BaseModel):
    """DNS 记录响应模型"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    zone: str
    hostname: str
    ip_address: str
    record_type: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class PaginationInfo(BaseModel):
    """分页信息"""

    total: int
    page: int
    page_size: int
    pages: int


class DNSRecordListResponse(BaseModel):
    """DNS 记录列表响应模型"""

    success: bool = True
    data: List[DNSRecordResponse]
    pagination: PaginationInfo


class DNSRecordCreateResponse(BaseModel):
    """DNS 记录创建响应"""

    success: bool = True
    data: DNSRecordResponse
    message: str


class DNSRecordUpdateResponse(BaseModel):
    """DNS 记录更新响应"""

    success: bool = True
    data: DNSRecordResponse
    message: str


class DNSRecordDeleteResponse(BaseModel):
    """DNS 记录删除响应"""

    success: bool = True
    message: str
    mode: str


class DNSZoneInfo(BaseModel):
    """Zone 信息模型"""

    name: str
    total_records: int
    active_records: int
    inactive_records: int


class DNSZoneListResponse(BaseModel):
    """Zone 列表响应"""

    success: bool = True
    data: List[DNSZoneInfo]


class DNSRecordSearchParams(BaseModel):
    """搜索参数模型"""

    q: Optional[str] = Field(None, description="全文搜索关键词")
    zone: Optional[str] = Field(None, description="Zone 精确匹配")
    hostname: Optional[str] = Field(None, description="主机名模糊匹配")
    ip: Optional[str] = Field(None, description="IP 地址模糊匹配")
    record_type: Optional[str] = Field(None, description="记录类型")
    status: Optional[str] = Field(None, description="状态")

    created_after: Optional[datetime] = Field(None, description="创建时间晚于")
    created_before: Optional[datetime] = Field(None, description="创建时间早于")
    updated_after: Optional[datetime] = Field(None, description="更新时间晚于")
    updated_before: Optional[datetime] = Field(None, description="更新时间早于")

    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

    sort_by: str = Field("created_at", description="排序字段")
    order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")


class DNSRecordSearchResponse(BaseModel):
    """搜索响应模型"""

    success: bool = True
    data: List[DNSRecordResponse]
    pagination: PaginationInfo
    filters_applied: Dict[str, str]
