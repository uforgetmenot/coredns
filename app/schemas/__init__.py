"""
Pydantic schemas for request/response models
"""

from app.schemas.dns_record import (
    DNSRecordResponse,
    PaginationInfo,
    DNSRecordListResponse,
)

__all__ = [
    "DNSRecordResponse",
    "PaginationInfo",
    "DNSRecordListResponse",
]
