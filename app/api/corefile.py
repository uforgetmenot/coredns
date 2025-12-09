"""Corefile API routes"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.schemas.backup import (
    BackupDetailResponse,
    BackupListResponse,
    DeleteBackupResponse,
    RestoreResponse,
)
from app.schemas.corefile import CorefileGenerateResponse, CorefilePreviewResponse
from app.services.backup_service import BackupService
from app.services.corefile_service import CorefileService

router = APIRouter(prefix="/api/corefile", tags=["Corefile"])


@router.post("/generate", response_model=CorefileGenerateResponse)
async def generate_corefile(session: Session = Depends(get_session)):
    service = CorefileService()
    try:
        result = service.generate_corefile(
            session=session,
            output_path=settings.corefile_path,
        )
        return {
            "success": True,
            "data": result,
            "message": "Corefile generated successfully",
        }
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/preview", response_model=CorefilePreviewResponse)
async def preview_corefile(session: Session = Depends(get_session)):
    service = CorefileService()
    result = service.generate_corefile(session=session)
    return {
        "success": True,
        "data": result,
    }


@router.post("/backups", response_model=BackupDetailResponse)
async def create_backup():
    """Create a manual backup of the current Corefile"""
    service = BackupService(settings.corefile_path)
    try:
        result = service.create_backup()
        return {"success": True, "data": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except OSError as exc:
        raise HTTPException(status_code=507, detail=str(exc))  # Insufficient Storage
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/backups", response_model=BackupListResponse)
async def list_backups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    service = BackupService(settings.corefile_path)
    try:
        result = service.list_backups(page=page, page_size=page_size)
        return {"success": True, "data": result}
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/backups/{backup_id}", response_model=BackupDetailResponse)
async def get_backup(backup_id: str):
    service = BackupService(settings.corefile_path)
    try:
        result = service.get_backup(backup_id)
        return {"success": True, "data": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/restore/{backup_id}", response_model=RestoreResponse)
async def restore_backup(backup_id: str):
    service = BackupService(settings.corefile_path)
    try:
        result = service.restore_backup(backup_id)
        return {
            "success": True,
            "data": result,
            "message": f"Backup {backup_id} restored successfully",
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/backups/{backup_id}", response_model=DeleteBackupResponse)
async def delete_backup(backup_id: str):
    service = BackupService(settings.corefile_path)
    try:
        service.delete_backup(backup_id)
        return {"success": True, "message": f"Backup {backup_id} deleted successfully"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))
