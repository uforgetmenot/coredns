# -*- coding: utf-8 -*-
"""
DNS Records API Router
提供 DNS 记录的 CRUD 操作
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.database import get_session
from app.schemas.dns_record import (
    DNSRecordCreate,
    DNSRecordCreateResponse,
    DNSRecordDeleteResponse,
    DNSRecordListResponse,
    DNSRecordPatch,
    DNSRecordSearchParams,
    DNSRecordSearchResponse,
    DNSRecordUpdate,
    DNSRecordUpdateResponse,
    DNSZoneListResponse,
    PaginationInfo,
)
from app.services.dns_service import DNSService

router = APIRouter(prefix="/api/records", tags=["DNS Records"])


@router.post("", response_model=DNSRecordCreateResponse, status_code=201)
async def create_record(
    record: DNSRecordCreate,
    session: Session = Depends(get_session),
):
    """创建新的 DNS 记录"""

    try:
        db_record = DNSService.create_record(session=session, record_data=record)
        return {
            "success": True,
            "data": db_record,
            "message": "DNS record created successfully",
        }
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/{record_id}", response_model=DNSRecordUpdateResponse)
async def update_record(
    record_id: int,
    record: DNSRecordUpdate,
    session: Session = Depends(get_session),
):
    """完整更新 DNS 记录"""

    try:
        db_record = DNSService.update_record(
            session=session, record_id=record_id, record_data=record
        )
        return {
            "success": True,
            "data": db_record,
            "message": "DNS record updated successfully",
        }
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/{record_id}", response_model=DNSRecordUpdateResponse)
async def patch_record(
    record_id: int,
    record: DNSRecordPatch,
    session: Session = Depends(get_session),
):
    """部分更新 DNS 记录"""

    try:
        db_record = DNSService.patch_record(
            session=session, record_id=record_id, record_data=record
        )
        return {
            "success": True,
            "data": db_record,
            "message": "DNS record updated successfully",
        }
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{record_id}", response_model=DNSRecordDeleteResponse)
async def delete_record(
    record_id: int,
    mode: str = Query(
        "soft",
        pattern="^(soft|hard)$",
        description="删除模式：soft（软删除）或 hard（硬删除）",
    ),
    session: Session = Depends(get_session),
):
    """删除 DNS 记录"""

    try:
        result = DNSService.delete_record(session=session, record_id=record_id, mode=mode)
        return {
            "success": True,
            **result,
        }
    except HTTPException as exc:
        raise exc
    except Exception as exc:  # pragma: no cover - unexpected errors
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", response_model=DNSRecordListResponse)
async def list_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    zone: Optional[str] = Query(None, description="Zone 过滤"),
    status: Optional[str] = Query(None, description="状态过滤（active/inactive/deleted）"),
    search: Optional[str] = Query(None, description="搜索关键词（hostname, ip_address）"),
    sort_by: str = Query("created_at", description="排序字段（zone, hostname, ip_address, created_at）"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    include_deleted: bool = Query(False, description="是否包含已删除的记录"),
    session: Session = Depends(get_session),
):
    """
    获取 DNS 记录列表

    支持的功能:
    - 分页: page, page_size
    - 过滤: zone, status, search
    - 排序: sort_by, order

    返回格式:
    - success: 请求是否成功
    - data: DNS 记录列表
    - pagination: 分页信息（total, page, page_size, pages）
    """
    records, total = DNSService.list_records(
        session=session,
        page=page,
        page_size=page_size,
        zone=zone,
        status=status,
        search=search,
        sort_by=sort_by,
        order=order,
        include_deleted=include_deleted,
    )

    pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "success": True,
        "data": records,
        "pagination": PaginationInfo(
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    }


@router.get("/zones", response_model=DNSZoneListResponse)
async def list_zones(
    search: Optional[str] = Query(None, description="Zone 名称搜索"),
    include_deleted: bool = Query(False, description="是否包含已删除状态的记录"),
    session: Session = Depends(get_session),
):
    """获取 Zone 列表，用于前端快速过滤"""

    zones = DNSService.list_zones(
        session=session,
        search=search,
        include_deleted=include_deleted,
    )

    return {
        "success": True,
        "data": zones,
    }


@router.get("/search", response_model=DNSRecordSearchResponse)
async def search_records(
    params: DNSRecordSearchParams = Depends(),
    session: Session = Depends(get_session),
):
    """高级搜索 DNS 记录"""

    records, total, filters_applied = DNSService.search_records(session=session, params=params)

    pages = math.ceil(total / params.page_size) if total > 0 else 0

    return {
        "success": True,
        "data": records,
        "pagination": PaginationInfo(
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages,
        ),
        "filters_applied": filters_applied,
    }
