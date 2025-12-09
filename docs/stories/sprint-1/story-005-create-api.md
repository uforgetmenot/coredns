# Story-005: DNS 记录创建 API

## 基本信息
- **故事ID**: Story-005
- **所属Sprint**: Sprint 1
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 通过 API 创建新的 DNS 记录
**So that** 可以快速添加新的域名解析配置

## 背景描述
DNS 记录创建是核心功能之一，需要支持完整的数据验证、重复检查和事务处理。创建成功后需要触发 Corefile 更新。

## 验收标准

- [x] AC1: POST `/api/records` 端点已实现
  - 接收 JSON 格式的记录数据
  - 验证所有必需字段
  - 返回 201 状态码和创建的记录

- [x] AC2: 请求体验证
  - `zone`: 必需，DNS Zone（如 seadee.com.cn）
  - `hostname`: 必需，主机名（如 app, www）
  - `ip_address`: 必需，IPv4 地址格式验证
  - `record_type`: 可选，默认 A，支持 A/AAAA/CNAME
  - `description`: 可选，记录描述
  - `status`: 可选，默认 active

- [x] AC3: 数据验证规则
  - IP 地址格式必须正确（IPv4: xxx.xxx.xxx.xxx）
  - hostname 不能包含特殊字符（允许字母、数字、连字符）
  - zone + hostname 的组合必须唯一
  - record_type 必须是允许的类型之一

- [x] AC4: 重复检查
  - 创建前检查是否已存在相同的 zone + hostname
  - 如果存在，返回 409 Conflict 错误
  - 错误信息明确说明冲突原因

- [x] AC5: 响应格式符合规范
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "zone": "seadee.com.cn",
      "hostname": "app",
      "ip_address": "172.27.0.3",
      "record_type": "A",
      "description": "Application server",
      "status": "active",
      "created_at": "2025-11-26T10:00:00Z",
      "updated_at": "2025-11-26T10:00:00Z"
    },
    "message": "DNS record created successfully"
  }
  ```

- [x] AC6: 错误处理完善
  - 400 Bad Request: 数据验证失败
  - 409 Conflict: 记录已存在
  - 500 Internal Server Error: 服务器错误

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试成功创建
  - 测试数据验证
  - 测试重复检查
  - 测试错误处理

## 技术实现要点

### 1. Pydantic 请求模型（app/schemas/dns_record.py）
```python
from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class DNSRecordCreate(BaseModel):
    zone: str = Field(..., min_length=1, max_length=255, description="DNS Zone")
    hostname: str = Field(..., min_length=1, max_length=255, description="主机名")
    ip_address: str = Field(..., description="IP 地址")
    record_type: str = Field("A", description="记录类型")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    status: str = Field("active", description="状态")

    @validator("ip_address")
    def validate_ip(cls, v):
        # 简单的 IPv4 验证
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IPv4 address format")

        parts = v.split(".")
        if not all(0 <= int(part) <= 255 for part in parts):
            raise ValueError("IPv4 address parts must be between 0 and 255")

        return v

    @validator("hostname")
    def validate_hostname(cls, v):
        # 主机名验证：字母、数字、连字符
        pattern = r"^[a-zA-Z0-9-]+$"
        if not re.match(pattern, v):
            raise ValueError("Hostname can only contain letters, numbers, and hyphens")
        return v

    @validator("record_type")
    def validate_record_type(cls, v):
        allowed_types = ["A", "AAAA", "CNAME"]
        if v not in allowed_types:
            raise ValueError(f"Record type must be one of: {', '.join(allowed_types)}")
        return v

    @validator("status")
    def validate_status(cls, v):
        allowed_statuses = ["active", "inactive"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

class DNSRecordCreateResponse(BaseModel):
    success: bool = True
    data: DNSRecordResponse
    message: str
```

### 2. Service 层（app/services/dns_service.py）
```python
from sqlmodel import Session, select
from app.models.dns_record import DNSRecord
from app.schemas.dns_record import DNSRecordCreate
from fastapi import HTTPException

class DNSService:
    @staticmethod
    def create_record(session: Session, record_data: DNSRecordCreate) -> DNSRecord:
        # 检查是否已存在
        existing = session.exec(
            select(DNSRecord).where(
                DNSRecord.zone == record_data.zone,
                DNSRecord.hostname == record_data.hostname,
                DNSRecord.status != "deleted"
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"DNS record already exists: {record_data.hostname}.{record_data.zone}"
            )

        # 创建新记录
        db_record = DNSRecord(**record_data.dict())
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
from app.schemas.dns_record import DNSRecordCreate, DNSRecordCreateResponse

router = APIRouter(prefix="/api/records", tags=["DNS Records"])

@router.post("", response_model=DNSRecordCreateResponse, status_code=201)
async def create_record(
    record: DNSRecordCreate,
    session: Session = Depends(get_session)
):
    """创建新的 DNS 记录"""
    try:
        db_record = DNSService.create_record(session, record)
        return {
            "success": True,
            "data": db_record,
            "message": "DNS record created successfully"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要 DNSRecord 模型)
- **后置依赖**:
  - Story-009 (Corefile 生成需要在记录创建后触发)
  - Story-014 (Web 表单需要调用此 API)

## 测试用例

### 测试场景 1: 成功创建记录
```python
def test_create_record_success():
    data = {
        "zone": "seadee.com.cn",
        "hostname": "test",
        "ip_address": "172.27.0.10",
        "record_type": "A",
        "description": "Test server"
    }
    response = client.post("/api/records", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["success"] is True
    assert result["data"]["hostname"] == "test"
    assert result["data"]["zone"] == "seadee.com.cn"
```

### 测试场景 2: IP 地址格式验证
```python
def test_create_record_invalid_ip():
    data = {
        "zone": "seadee.com.cn",
        "hostname": "test",
        "ip_address": "invalid.ip",
        "record_type": "A"
    }
    response = client.post("/api/records", json=data)
    assert response.status_code == 422  # Validation error
```

### 测试场景 3: 重复记录检查
```python
def test_create_duplicate_record():
    data = {
        "zone": "seadee.com.cn",
        "hostname": "duplicate",
        "ip_address": "172.27.0.11"
    }
    # 第一次创建
    response1 = client.post("/api/records", json=data)
    assert response1.status_code == 201

    # 第二次创建（重复）
    response2 = client.post("/api/records", json=data)
    assert response2.status_code == 409  # Conflict
```

### 测试场景 4: 主机名验证
```python
def test_create_record_invalid_hostname():
    data = {
        "zone": "seadee.com.cn",
        "hostname": "test@invalid",
        "ip_address": "172.27.0.12"
    }
    response = client.post("/api/records", json=data)
    assert response.status_code == 422
```

### 测试场景 5: 必需字段验证
```python
def test_create_record_missing_fields():
    data = {
        "zone": "seadee.com.cn"
        # 缺少 hostname 和 ip_address
    }
    response = client.post("/api/records", json=data)
    assert response.status_code == 422
```

## 完成定义 (Definition of Done)
- [x] API 端点已实现
- [x] 所有验收标准已满足
- [x] Service 层业务逻辑已实现
- [x] Pydantic 模型已定义并包含验证
- [x] 重复检查逻辑已实现
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
