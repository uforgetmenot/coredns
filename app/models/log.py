"""
操作日志数据模型
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class OperationLog(SQLModel, table=True):
    """
    操作日志模型

    记录所有对 DNS 记录和系统配置的操作
    """

    __tablename__ = "operation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    operation_type: str = Field(
        index=True,
        max_length=50,
        description="操作类型（create, update, delete, reload）",
    )
    resource_type: str = Field(
        index=True,
        max_length=50,
        description="资源类型（record, zone, corefile, setting）",
    )
    resource_id: Optional[int] = Field(default=None, description="资源 ID")
    details: str = Field(description="操作详情（JSON 格式）")
    user: str = Field(default="admin", max_length=100, description="操作用户")
    ip_address: Optional[str] = Field(
        default=None, max_length=45, description="操作 IP"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="操作时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "operation_type": "create",
                "resource_type": "record",
                "resource_id": 1,
                "details": '{"zone": "example.com", "hostname": "www"}',
                "user": "admin",
                "ip_address": "192.168.1.1",
            }
        }
