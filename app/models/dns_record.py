"""
DNS 记录数据模型
"""

from sqlmodel import SQLModel, Field, Index
from typing import Optional
from datetime import datetime, timezone


class DNSRecord(SQLModel, table=True):
    """
    DNS 记录模型

    存储 DNS 解析记录，包括域名、IP 地址和记录类型等信息
    """

    __tablename__ = "dns_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    zone: str = Field(
        index=True, max_length=255, description="域名区域（如 example.com）"
    )
    hostname: str = Field(index=True, max_length=255, description="主机名（如 www）")
    ip_address: str = Field(
        index=True, max_length=45, description="IP 地址（IPv4 或 IPv6）"
    )
    record_type: str = Field(
        default="A",
        max_length=10,
        description="记录类型（A, AAAA, CNAME 等）",
        index=True,
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="记录说明"
    )
    status: str = Field(
        default="active",
        max_length=20,
        description="状态（active, inactive, deleted）",
        index=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="更新时间",
        index=True,
    )

    __table_args__ = (
        Index("idx_zone_hostname", "zone", "hostname"),
        Index("idx_status_created", "status", "created_at"),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "zone": "seadee.com.cn",
                "hostname": "app",
                "ip_address": "172.27.0.3",
                "record_type": "A",
                "description": "Application server",
                "status": "active",
            }
        }
