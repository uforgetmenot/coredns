"""
Zone 配置数据模型
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class Zone(SQLModel, table=True):
    """
    DNS Zone 配置模型

    存储 DNS Zone 的配置信息，包括名称、上游 DNS 等
    """

    __tablename__ = "zones"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        unique=True,
        index=True,
        max_length=255,
        description="Zone 名称（如 example.com）",
    )
    fallthrough: bool = Field(default=True, description="是否启用 fallthrough")
    log_enabled: bool = Field(default=True, description="是否启用日志")
    upstream_dns: Optional[str] = Field(
        default=None, max_length=255, description="上游 DNS 服务器地址"
    )
    status: str = Field(
        default="active", max_length=20, description="状态（active, inactive）"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="更新时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "seadee.com.cn",
                "fallthrough": True,
                "log_enabled": True,
                "upstream_dns": "223.5.5.5",
                "status": "active",
            }
        }
