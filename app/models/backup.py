"""
Corefile 备份数据模型
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class CorefileBackup(SQLModel, table=True):
    """
    Corefile 备份模型

    存储 Corefile 的历史备份，用于版本管理和回滚
    """

    __tablename__ = "corefile_backups"

    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(description="Corefile 完整内容")
    backup_reason: str = Field(max_length=255, description="备份原因")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="备份时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": ". {\\n  forward . 8.8.8.8\\n}",
                "backup_reason": "Before adding new DNS record",
            }
        }
