"""
DNS Service Layer - Business logic for DNS record operations
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import case
from sqlmodel import Session, select, func, or_

from app.models.dns_record import DNSRecord
from app.schemas.dns_record import (
    DNSRecordCreate,
    DNSRecordPatch,
    DNSRecordSearchParams,
    DNSRecordUpdate,
)


class DNSService:
    """DNS 记录服务层"""

    @staticmethod
    def create_record(session: Session, record_data: DNSRecordCreate) -> DNSRecord:
        """创建新的 DNS 记录，包含重复检查"""

        existing = session.exec(
            select(DNSRecord).where(
                DNSRecord.zone == record_data.zone,
                DNSRecord.hostname == record_data.hostname,
                DNSRecord.status != "deleted",
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"DNS record already exists: {record_data.hostname}.{record_data.zone}",
            )

        db_record = DNSRecord(**record_data.model_dump())
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        return db_record

    @staticmethod
    def update_record(
        session: Session, record_id: int, record_data: DNSRecordUpdate
    ) -> DNSRecord:
        """完整更新 DNS 记录"""

        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        if db_record.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot update deleted record")

        existing = session.exec(
            select(DNSRecord).where(
                DNSRecord.zone == record_data.zone,
                DNSRecord.hostname == record_data.hostname,
                DNSRecord.id != record_id,
                DNSRecord.status != "deleted",
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=(
                    "DNS record conflicts with existing record: "
                    f"{record_data.hostname}.{record_data.zone}"
                ),
            )

        update_payload = record_data.model_dump()
        for key, value in update_payload.items():
            setattr(db_record, key, value)

        db_record.updated_at = datetime.now(timezone.utc)
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        return db_record

    @staticmethod
    def patch_record(
        session: Session, record_id: int, record_data: DNSRecordPatch
    ) -> DNSRecord:
        """部分更新 DNS 记录"""

        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        if db_record.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot update deleted record")

        update_data = record_data.model_dump(exclude_unset=True)

        if "zone" in update_data or "hostname" in update_data:
            new_zone = update_data.get("zone", db_record.zone)
            new_hostname = update_data.get("hostname", db_record.hostname)

            existing = session.exec(
                select(DNSRecord).where(
                    DNSRecord.zone == new_zone,
                    DNSRecord.hostname == new_hostname,
                    DNSRecord.id != record_id,
                    DNSRecord.status != "deleted",
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "DNS record conflicts with existing record: "
                        f"{new_hostname}.{new_zone}"
                    ),
                )

        for key, value in update_data.items():
            setattr(db_record, key, value)

        db_record.updated_at = datetime.now(timezone.utc)
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        return db_record

    @staticmethod
    def delete_record(session: Session, record_id: int, mode: str = "soft") -> dict:
        """删除 DNS 记录，支持软删除或硬删除"""

        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        mode = mode.lower()

        if mode == "soft":
            if db_record.status == "deleted":
                raise HTTPException(status_code=400, detail="Record is already deleted")

            db_record.status = "deleted"
            db_record.updated_at = datetime.now(timezone.utc)
            session.add(db_record)
            session.commit()
            session.refresh(db_record)

            return {
                "message": "DNS record deleted successfully",
                "mode": "soft",
            }

        if mode == "hard":
            session.delete(db_record)
            session.commit()

            return {
                "message": "DNS record permanently deleted",
                "mode": "hard",
            }

        raise HTTPException(
            status_code=400, detail="Invalid delete mode. Use 'soft' or 'hard'"
        )

    @staticmethod
    def list_records(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        zone: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        include_deleted: bool = False,
    ) -> Tuple[List[DNSRecord], int]:
        """
        获取 DNS 记录列表

        Args:
            session: 数据库会话
            page: 页码（从 1 开始）
            page_size: 每页记录数
            zone: Zone 过滤（精确匹配）
            status: 状态过滤
            search: 搜索关键词（模糊匹配 hostname 或 ip_address）
            sort_by: 排序字段
            order: 排序方向（asc/desc）

        Returns:
            (records, total): 记录列表和总数
        """
        # 构建基础查询
        query = select(DNSRecord)

        if not include_deleted:
            query = query.where(DNSRecord.status != "deleted")

        # 应用过滤条件
        if zone:
            query = query.where(DNSRecord.zone == zone)

        if status:
            query = query.where(DNSRecord.status == status)

        if search:
            query = query.where(
                or_(
                    DNSRecord.hostname.contains(search),
                    DNSRecord.ip_address.contains(search),
                )
            )

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()

        # 应用排序
        order_column = getattr(DNSRecord, sort_by, DNSRecord.created_at)
        if order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        records = session.exec(query).all()

        return records, total

    @staticmethod
    def list_zones(
        session: Session,
        search: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[Dict[str, int | str]]:
        """返回 Zone 聚合信息，用于快速筛选"""

        query = select(
            DNSRecord.zone.label("name"),
            func.count().label("total_records"),
            func.sum(case((DNSRecord.status == "active", 1), else_=0)).label(
                "active_records"
            ),
            func.sum(case((DNSRecord.status == "inactive", 1), else_=0)).label(
                "inactive_records"
            ),
        )

        if not include_deleted:
            query = query.where(DNSRecord.status != "deleted")

        if search:
            query = query.where(DNSRecord.zone.contains(search))

        query = query.group_by(DNSRecord.zone).order_by(func.count().desc(), DNSRecord.zone)

        rows = session.exec(query).all()

        return [
            {
                "name": row.name,
                "total_records": row.total_records,
                "active_records": row.active_records or 0,
                "inactive_records": row.inactive_records or 0,
            }
            for row in rows
        ]

    @staticmethod
    def search_records(
        session: Session, params: DNSRecordSearchParams
    ) -> Tuple[List[DNSRecord], int, Dict[str, str]]:
        """搜索 DNS 记录，支持多条件过滤"""

        query = select(DNSRecord).where(DNSRecord.status != "deleted")
        filters_applied: Dict[str, str] = {}

        if params.q:
            query = query.where(
                or_(
                    DNSRecord.hostname.contains(params.q),
                    DNSRecord.ip_address.contains(params.q),
                    DNSRecord.description.contains(params.q),
                )
            )
            filters_applied["q"] = params.q

        if params.zone:
            query = query.where(DNSRecord.zone == params.zone)
            filters_applied["zone"] = params.zone

        if params.hostname:
            query = query.where(DNSRecord.hostname.contains(params.hostname))
            filters_applied["hostname"] = params.hostname

        if params.ip:
            query = query.where(DNSRecord.ip_address.contains(params.ip))
            filters_applied["ip"] = params.ip

        if params.record_type:
            query = query.where(DNSRecord.record_type == params.record_type)
            filters_applied["record_type"] = params.record_type

        if params.status:
            query = query.where(DNSRecord.status == params.status)
            filters_applied["status"] = params.status

        if params.created_after:
            query = query.where(DNSRecord.created_at >= params.created_after)
            filters_applied["created_after"] = params.created_after.isoformat()

        if params.created_before:
            query = query.where(DNSRecord.created_at <= params.created_before)
            filters_applied["created_before"] = params.created_before.isoformat()

        if params.updated_after:
            query = query.where(DNSRecord.updated_at >= params.updated_after)
            filters_applied["updated_after"] = params.updated_after.isoformat()

        if params.updated_before:
            query = query.where(DNSRecord.updated_at <= params.updated_before)
            filters_applied["updated_before"] = params.updated_before.isoformat()

        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()

        order_column = getattr(DNSRecord, params.sort_by, DNSRecord.created_at)
        if params.order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        records = session.exec(query).all()

        return records, total, filters_applied
