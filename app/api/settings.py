"""Settings API routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.schemas.settings import (
    UpdateUpstreamDNSRequest,
    UpstreamDNSResponse,
    UpstreamDNSSettings,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/upstream-dns", response_model=UpstreamDNSResponse)
async def get_upstream_dns(session: Session = Depends(get_session)):
    """获取上级 DNS 配置"""
    try:
        service = SettingsService(session)
        primary, secondary = service.get_upstream_dns()
        return {
            "success": True,
            "data": UpstreamDNSSettings(
                primary_dns=primary,
                secondary_dns=secondary,
            ),
            "message": "Upstream DNS settings retrieved successfully",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/upstream-dns", response_model=UpstreamDNSResponse)
async def update_upstream_dns(
    request: UpdateUpstreamDNSRequest,
    session: Session = Depends(get_session),
):
    """更新上级 DNS 配置"""
    try:
        service = SettingsService(session)
        primary, secondary = service.set_upstream_dns(
            request.primary_dns,
            request.secondary_dns,
        )
        return {
            "success": True,
            "data": UpstreamDNSSettings(
                primary_dns=primary,
                secondary_dns=secondary,
            ),
            "message": "Upstream DNS settings updated successfully",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
