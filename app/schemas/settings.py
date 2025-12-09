"""Settings schemas"""

from typing import Optional
from pydantic import BaseModel, Field, validator

from app.config import settings


class UpstreamDNSSettings(BaseModel):
    """上级 DNS 配置"""

    primary_dns: str = Field(
        default=settings.upstream_primary_dns_default,
        description="主 DNS 服务器地址",
        max_length=45,
    )
    secondary_dns: Optional[str] = Field(
        default=settings.upstream_secondary_dns_default,
        description="备用 DNS 服务器地址（可选）",
        max_length=45,
    )

    @validator("primary_dns", "secondary_dns")
    def validate_dns_address(cls, v):
        """验证 DNS 地址格式"""
        if v is None or v == "":
            return v
        # 简单验证：包含点号或冒号（IPv4 或 IPv6）
        if "." not in v and ":" not in v:
            raise ValueError("Invalid DNS address format")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "primary_dns": settings.upstream_primary_dns_default,
                "secondary_dns": settings.upstream_secondary_dns_default,
            }
        }


class UpstreamDNSResponse(BaseModel):
    """上级 DNS 响应"""

    success: bool = True
    data: UpstreamDNSSettings
    message: str = "Success"


class UpdateUpstreamDNSRequest(BaseModel):
    """更新上级 DNS 请求"""

    primary_dns: str = Field(
        ...,
        description="主 DNS 服务器地址",
        max_length=45,
    )
    secondary_dns: Optional[str] = Field(
        default=None,
        description="备用 DNS 服务器地址（可选）",
        max_length=45,
    )

    @validator("primary_dns", "secondary_dns")
    def validate_dns_address(cls, v):
        """验证 DNS 地址格式"""
        if v is None or v == "":
            return v
        # 简单验证：包含点号或冒号（IPv4 或 IPv6）
        if "." not in v and ":" not in v:
            raise ValueError("Invalid DNS address format")
        return v.strip()
