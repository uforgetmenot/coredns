"""CoreDNS control API"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.coredns import CoreDNSReloadResponse, CoreDNSStatusResponse
from app.services.coredns_service import CoreDNSService

router = APIRouter(prefix="/api/coredns", tags=["CoreDNS"])


@router.post("/reload", response_model=CoreDNSReloadResponse)
async def reload_coredns():
    service = CoreDNSService()

    if not service.validate_corefile(settings.corefile_path):
        raise HTTPException(status_code=400, detail="Corefile is invalid or missing")

    try:
        result = service.reload()
        return {
            "success": True,
            "data": result,
            "message": "CoreDNS reloaded successfully",
        }
    except Exception as exc:  # pragma: no cover - system-specific
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status", response_model=CoreDNSStatusResponse)
async def get_coredns_status():
    service = CoreDNSService()
    try:
        status = service.get_status()
        status["corefile_path"] = settings.corefile_path
        return {"success": True, "data": status}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))
