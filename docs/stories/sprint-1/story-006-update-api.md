# Story-006: DNS 记录更新 API

## 基本信息
- **故事ID**: Story-006
- **所属Sprint**: Sprint 1
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 通过 API 更新已存在的 DNS 记录
**So that** 可以修改域名解析配置而不需要删除重建

## 背景描述
DNS 记录更新是日常运维中的常见操作，需要支持部分更新（PATCH）和完整更新（PUT）两种方式。更新成功后需要触发 Corefile 重新生成。

## 验收标准

- [x] AC1: PUT `/api/records/{id}` 端点已实现
  - 支持完整更新记录
  - 接收记录 ID 作为路径参数
  - 返回 200 状态码和更新后的记录

- [x] AC2: PATCH `/api/records/{id}` 端点已实现
  - 支持部分字段更新
  - 只更新提供的字段，其他字段保持不变
  - 返回 200 状态码和更新后的记录

- [x] AC3: 请求体验证
  - `zone`: 可更新，格式验证
  - `hostname`: 可更新，格式验证
  - `ip_address`: 可更新，IPv4 格式验证
  - `record_type`: 可更新，类型验证
  - `description`: 可更新
  - `status`: 可更新，状态验证

- [x] AC4: 业务逻辑验证
  - 记录 ID 必须存在，否则返回 404
  - 更新后的 zone + hostname 组合不能与其他记录冲突
  - 不能更新已删除的记录（status = deleted）
  - 自动更新 updated_at 时间戳

- [x] AC5: 响应格式符合规范
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "zone": "seadee.com.cn",
      "hostname": "app-new",
      "ip_address": "172.27.0.4",
      "record_type": "A",
      "description": "Updated application server",
      "status": "active",
      "created_at": "2025-11-26T10:00:00Z",
      "updated_at": "2025-11-26T11:00:00Z"
    },
    "message": "DNS record updated successfully"
  }
  ```

- [x] AC6: 错误处理完善
  - 400 Bad Request: 数据验证失败
  - 404 Not Found: 记录不存在
  - 409 Conflict: 更新后的记录与其他记录冲突
  - 500 Internal Server Error: 服务器错误

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试完整更新（PUT）
  - 测试部分更新（PATCH）
  - 测试记录不存在
  - 测试冲突检查
  - 测试数据验证

## 技术实现要点

### 1. Pydantic 请求模型（app/schemas/dns_record.py）
```python
from pydantic import BaseModel, validator
from typing import Optional

class DNSRecordUpdate(BaseModel):
    """完整更新模型（PUT）"""
    zone: str
    hostname: str
    ip_address: str
    record_type: str = "A"
    description: Optional[str] = None
    status: str = "active"

    # 使用与 DNSRecordCreate 相同的验证器
    @validator("ip_address")
    def validate_ip(cls, v):
        # IP 验证逻辑
        pass

    @validator("hostname")
    def validate_hostname(cls, v):
        # 主机名验证逻辑
        pass

class DNSRecordPatch(BaseModel):
    """部分更新模型（PATCH）"""
    zone: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    record_type: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

    @validator("ip_address")
    def validate_ip(cls, v):
        if v is not None:
            # IP 验证逻辑
            pass
        return v

    @validator("hostname")
    def validate_hostname(cls, v):
        if v is not None:
            # 主机名验证逻辑
            pass
        return v

class DNSRecordUpdateResponse(BaseModel):
    success: bool = True
    data: DNSRecordResponse
    message: str
```

### 2. Service 层（app/services/dns_service.py）
```python
from sqlmodel import Session, select
from app.models.dns_record import DNSRecord
from app.schemas.dns_record import DNSRecordUpdate, DNSRecordPatch
from fastapi import HTTPException
from datetime import datetime

class DNSService:
    @staticmethod
    def update_record(
        session: Session,
        record_id: int,
        record_data: DNSRecordUpdate
    ) -> DNSRecord:
        # 查找记录
        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        if db_record.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot update deleted record")

        # 检查冲突（排除当前记录）
        existing = session.exec(
            select(DNSRecord).where(
                DNSRecord.zone == record_data.zone,
                DNSRecord.hostname == record_data.hostname,
                DNSRecord.id != record_id,
                DNSRecord.status != "deleted"
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"DNS record conflicts with existing record: {record_data.hostname}.{record_data.zone}"
            )

        # 更新字段
        for key, value in record_data.dict().items():
            setattr(db_record, key, value)

        db_record.updated_at = datetime.utcnow()
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        return db_record

    @staticmethod
    def patch_record(
        session: Session,
        record_id: int,
        record_data: DNSRecordPatch
    ) -> DNSRecord:
        # 查找记录
        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        if db_record.status == "deleted":
            raise HTTPException(status_code=400, detail="Cannot update deleted record")

        # 准备更新数据
        update_data = record_data.dict(exclude_unset=True)

        # 如果更新了 zone 或 hostname，检查冲突
        if "zone" in update_data or "hostname" in update_data:
            new_zone = update_data.get("zone", db_record.zone)
            new_hostname = update_data.get("hostname", db_record.hostname)

            existing = session.exec(
                select(DNSRecord).where(
                    DNSRecord.zone == new_zone,
                    DNSRecord.hostname == new_hostname,
                    DNSRecord.id != record_id,
                    DNSRecord.status != "deleted"
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"DNS record conflicts with existing record: {new_hostname}.{new_zone}"
                )

        # 更新字段
        for key, value in update_data.items():
            setattr(db_record, key, value)

        db_record.updated_at = datetime.utcnow()
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        return db_record
```

### 3. API 路由（app/api/records.py）
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.services.dns_service import DNSService
from app.schemas.dns_record import (
    DNSRecordUpdate,
    DNSRecordPatch,
    DNSRecordUpdateResponse
)

router = APIRouter(prefix="/api/records", tags=["DNS Records"])

@router.put("/{record_id}", response_model=DNSRecordUpdateResponse)
async def update_record(
    record_id: int,
    record: DNSRecordUpdate,
    session: Session = Depends(get_session)
):
    """完整更新 DNS 记录"""
    db_record = DNSService.update_record(session, record_id, record)
    return {
        "success": True,
        "data": db_record,
        "message": "DNS record updated successfully"
    }

@router.patch("/{record_id}", response_model=DNSRecordUpdateResponse)
async def patch_record(
    record_id: int,
    record: DNSRecordPatch,
    session: Session = Depends(get_session)
):
    """部分更新 DNS 记录"""
    db_record = DNSService.patch_record(session, record_id, record)
    return {
        "success": True,
        "data": db_record,
        "message": "DNS record updated successfully"
    }
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要 DNSRecord 模型)
- **后置依赖**:
  - Story-009 (Corefile 生成需要在记录更新后触发)
  - Story-014 (Web 表单需要调用此 API)

## 测试用例

### 测试场景 1: 成功完整更新（PUT）
```python
def test_update_record_success():
    # 先创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "old",
        "ip_address": "172.27.0.10"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 更新记录
    update_data = {
        "zone": "seadee.com.cn",
        "hostname": "new",
        "ip_address": "172.27.0.11",
        "record_type": "A",
        "status": "active"
    }
    response = client.put(f"/api/records/{record_id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["data"]["hostname"] == "new"
    assert result["data"]["ip_address"] == "172.27.0.11"
```

### 测试场景 2: 成功部分更新（PATCH）
```python
def test_patch_record_success():
    # 先创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "test",
        "ip_address": "172.27.0.10"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 部分更新（只更新 IP）
    patch_data = {"ip_address": "172.27.0.20"}
    response = client.patch(f"/api/records/{record_id}", json=patch_data)
    assert response.status_code == 200
    result = response.json()
    assert result["data"]["ip_address"] == "172.27.0.20"
    assert result["data"]["hostname"] == "test"  # 未改变
```

### 测试场景 3: 记录不存在
```python
def test_update_nonexistent_record():
    update_data = {
        "zone": "seadee.com.cn",
        "hostname": "test",
        "ip_address": "172.27.0.10",
        "record_type": "A",
        "status": "active"
    }
    response = client.put("/api/records/99999", json=update_data)
    assert response.status_code == 404
```

### 测试场景 4: 更新冲突检查
```python
def test_update_conflict():
    # 创建两条记录
    data1 = {"zone": "seadee.com.cn", "hostname": "record1", "ip_address": "172.27.0.10"}
    data2 = {"zone": "seadee.com.cn", "hostname": "record2", "ip_address": "172.27.0.11"}

    response1 = client.post("/api/records", json=data1)
    response2 = client.post("/api/records", json=data2)

    record2_id = response2.json()["data"]["id"]

    # 尝试将 record2 更新为与 record1 相同的 hostname
    update_data = {
        "zone": "seadee.com.cn",
        "hostname": "record1",
        "ip_address": "172.27.0.12",
        "record_type": "A",
        "status": "active"
    }
    response = client.put(f"/api/records/{record2_id}", json=update_data)
    assert response.status_code == 409  # Conflict
```

### 测试场景 5: 不能更新已删除的记录
```python
def test_update_deleted_record():
    # 创建并删除记录
    create_data = {"zone": "seadee.com.cn", "hostname": "deleted", "ip_address": "172.27.0.10"}
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 标记为删除
    client.patch(f"/api/records/{record_id}", json={"status": "deleted"})

    # 尝试更新
    update_data = {"ip_address": "172.27.0.20"}
    response = client.patch(f"/api/records/{record_id}", json=update_data)
    assert response.status_code == 400
```

## 完成定义 (Definition of Done)
- [x] PUT 和 PATCH 端点已实现
- [x] 所有验收标准已满足
- [x] Service 层业务逻辑已实现
- [x] 冲突检查逻辑已实现
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [FastAPI Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [PUT vs PATCH](https://stackoverflow.com/questions/28459418/rest-api-put-vs-patch-with-real-life-examples)
- [Pydantic Partial Models](https://docs.pydantic.dev/latest/concepts/models/#partial-models)

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
