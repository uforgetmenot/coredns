"""
系统设置数据模型
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class SystemSetting(SQLModel, table=True):
    """
    系统设置模型

    存储系统配置参数，支持动态修改
    """

    __tablename__ = "system_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(
        unique=True,
        index=True,
        max_length=100,
        description="设置键（如 log_retention_days）",
    )
    value: str = Field(max_length=1000, description="设置值")
    description: Optional[str] = Field(
        default=None, max_length=500, description="设置说明"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="更新时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "key": "log_retention_days",
                "value": "30",
                "description": "日志保留天数",
            }
        }
