# Story-004: DNS 记录列表查询 API

## 基本信息
- **故事ID**: Story-004
- **所属Sprint**: Sprint 1
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Done

## 用户故事
**As a** 系统管理员
**I want** 通过 API 获取 DNS 记录列表
**So that** 可以查看和管理所有 DNS 配置

## 背景描述
DNS 记录列表查询是核心功能之一，需要支持分页、排序、按 Zone 过滤等功能。这个 API 将被 Web 界面和其他客户端调用。

## 验收标准

- [x] AC1: GET `/api/records` 端点已实现
  - 返回 DNS 记录列表
  - 默认按创建时间倒序排列
  - 返回 200 状态码

- [x] AC2: 支持分页参数
  - `page`: 页码（默认 1）
  - `page_size`: 每页记录数（默认 20，最大 100）
  - 返回数据包含分页信息（total, page, page_size, pages）

- [x] AC3: 支持过滤参数
  - `zone`: 按 Zone 过滤（精确匹配）
  - `status`: 按状态过滤（active/inactive/deleted）
  - `search`: 模糊搜索（hostname, ip_address）

- [x] AC4: 支持排序参数
  - `sort_by`: 排序字段（zone, hostname, ip_address, created_at）
  - `order`: 排序方向（asc/desc）

- [x] AC5: 响应格式符合规范
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 1,
        "zone": "seadee.com.cn",
        "hostname": "app",
        "ip_address": "172.27.0.3",
        "record_type": "A",
        "description": "Application server",
        "status": "active",
        "created_at": "2025-11-26T10:00:00Z",
        "updated_at": "2025-11-26T10:00:00Z"
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "page_size": 20,
      "pages": 5
    }
  }
  ```

- [x] AC6: API 文档已生成
  - Swagger UI 中可以看到完整的 API 文档
  - 包含请求参数说明
  - 包含响应示例

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试正常查询
  - 测试分页
  - 测试过滤
  - 测试排序
  - 测试边界条件

## 技术实现要点

### 1. Pydantic 响应模型（app/schemas/dns_record.py）
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class DNSRecordResponse(BaseModel):
    id: int
    zone: str
    hostname: str
    ip_address: str
    record_type: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginationInfo(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int

class DNSRecordListResponse(BaseModel):
    success: bool = True
    data: List[DNSRecordResponse]
    pagination: PaginationInfo
```

### 2. Service 层（app/services/dns_service.py）
```python
from sqlmodel import Session, select, func
from app.models.dns_record import DNSRecord
from typing import List, Optional

class DNSService:
    @staticmethod
    def list_records(
        session: Session,
        page: int = 1,
        page_size: int = 20,
        zone: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        order: str = "desc"
    ):
        # 构建查询
        query = select(DNSRecord)

        # 应用过滤
        if zone:
            query = query.where(DNSRecord.zone == zone)
        if status:
            query = query.where(DNSRecord.status == status)
        if search:
            query = query.where(
                (DNSRecord.hostname.contains(search)) |
                (DNSRecord.ip_address.contains(search))
            )

        # 计算总数
        total = session.exec(select(func.count()).select_from(query.subquery())).one()

        # 应用排序
        order_column = getattr(DNSRecord, sort_by)
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
```

### 3. API 路由（app/api/records.py）
```python
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.database import get_session
from app.services.dns_service import DNSService
from app.schemas.dns_record import DNSRecordListResponse, PaginationInfo
from typing import Optional
import math

router = APIRouter(prefix="/api/records", tags=["DNS Records"])

@router.get("", response_model=DNSRecordListResponse)
async def list_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页记录数"),
    zone: Optional[str] = Query(None, description="Zone 过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    sort_by: str = Query("created_at", description="排序字段"),
    order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    session: Session = Depends(get_session)
):
    """获取 DNS 记录列表"""
    records, total = DNSService.list_records(
        session=session,
        page=page,
        page_size=page_size,
        zone=zone,
        status=status,
        search=search,
        sort_by=sort_by,
        order=order
    )

    pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "success": True,
        "data": records,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
    }
```

### 4. 注册路由（app/main.py）
```python
from app.api import records

app.include_router(records.router)
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要 DNSRecord 模型)
- **后置依赖**:
  - Story-013 (Web 列表页面需要调用此 API)

## 测试用例

### 测试场景 1: 基本列表查询
```python
def test_list_records():
    response = client.get("/api/records")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data
```

### 测试场景 2: 分页功能
```python
def test_pagination():
    response = client.get("/api/records?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["page_size"] == 10
```

### 测试场景 3: Zone 过滤
```python
def test_filter_by_zone():
    response = client.get("/api/records?zone=seadee.com.cn")
    assert response.status_code == 200
    data = response.json()
    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"
```

### 测试场景 4: 搜索功能
```python
def test_search():
    response = client.get("/api/records?search=app")
    assert response.status_code == 200
    data = response.json()
    # 验证搜索结果包含关键词
    assert len(data["data"]) > 0
```

### 测试场景 5: 排序功能
```python
def test_sorting():
    response = client.get("/api/records?sort_by=hostname&order=asc")
    assert response.status_code == 200
    data = response.json()
    hostnames = [r["hostname"] for r in data["data"]]
    assert hostnames == sorted(hostnames)
```

## 完成定义 (Definition of Done)
- [x] API 端点已实现
- [x] 所有验收标准已满足
- [x] Service 层业务逻辑已实现
- [x] Pydantic 模型已定义
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [ ] 代码已合并到 `develop` 分支

## 参考资料
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [SQLModel Filtering](https://sqlmodel.tiangolo.com/tutorial/where/)
- [Pagination Best Practices](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Filtering-Sorting-and-Pagination/)

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
