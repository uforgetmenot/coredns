# Story-008: DNS 记录搜索和过滤 API

## 基本信息
- **故事ID**: Story-008
- **所属Sprint**: Sprint 1
- **优先级**: Medium
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 通过多种条件搜索和过滤 DNS 记录
**So that** 可以快速找到需要管理的特定记录

## 背景描述
在实际使用中，DNS 记录可能非常多，需要提供强大的搜索和过滤功能。这个功能是对 Story-004 列表 API 的增强，提供更丰富的查询能力。

## 验收标准

- [x] AC1: GET `/api/records/search` 端点已实现
  - 支持复杂的搜索和过滤条件
  - 返回符合条件的记录列表
  - 支持分页

- [x] AC2: 支持多种搜索方式
  - `q`: 全文搜索（搜索 hostname, ip_address, description）
  - `zone`: 精确匹配 Zone
  - `hostname`: 模糊匹配主机名
  - `ip`: 模糊匹配 IP 地址
  - `record_type`: 精确匹配记录类型
  - `status`: 精确匹配状态

- [x] AC3: 支持高级过滤
  - `created_after`: 创建时间晚于指定时间
  - `created_before`: 创建时间早于指定时间
  - `updated_after`: 更新时间晚于指定时间
  - `updated_before`: 更新时间早于指定时间

- [x] AC4: 支持多条件组合
  - 所有条件之间是 AND 关系
  - 可以同时使用多个过滤条件
  - 空值条件会被忽略

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
      "total": 50,
      "page": 1,
      "page_size": 20,
      "pages": 3
    },
    "filters_applied": {
      "q": "app",
      "zone": "seadee.com.cn",
      "status": "active"
    }
  }
  ```

- [x] AC6: 性能要求
  - 搜索响应时间 < 500ms（1000条记录内）
  - 支持数据库索引优化
  - 避免全表扫描

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试单条件搜索
  - 测试多条件组合
  - 测试时间范围过滤
  - 测试空结果
  - 测试性能

## 技术实现要点

### 1. Pydantic 请求模型（app/schemas/dns_record.py）
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DNSRecordSearchParams(BaseModel):
    """搜索参数模型"""
    # 基本搜索
    q: Optional[str] = Field(None, description="全文搜索关键词")
    zone: Optional[str] = Field(None, description="Zone 精确匹配")
    hostname: Optional[str] = Field(None, description="主机名模糊匹配")
    ip: Optional[str] = Field(None, description="IP 地址模糊匹配")
    record_type: Optional[str] = Field(None, description="记录类型")
    status: Optional[str] = Field(None, description="状态")

    # 时间范围过滤
    created_after: Optional[datetime] = Field(None, description="创建时间晚于")
    created_before: Optional[datetime] = Field(None, description="创建时间早于")
    updated_after: Optional[datetime] = Field(None, description="更新时间晚于")
    updated_before: Optional[datetime] = Field(None, description="更新时间早于")

    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页记录数")

    # 排序参数
    sort_by: str = Field("created_at", description="排序字段")
    order: str = Field("desc", regex="^(asc|desc)$", description="排序方向")

class DNSRecordSearchResponse(BaseModel):
    success: bool = True
    data: List[DNSRecordResponse]
    pagination: PaginationInfo
    filters_applied: dict
```

### 2. Service 层（app/services/dns_service.py）
```python
from sqlmodel import Session, select, func, or_, and_
from app.models.dns_record import DNSRecord
from app.schemas.dns_record import DNSRecordSearchParams
from typing import Tuple, List

class DNSService:
    @staticmethod
    def search_records(
        session: Session,
        params: DNSRecordSearchParams
    ) -> Tuple[List[DNSRecord], int, dict]:
        """
        搜索 DNS 记录

        Args:
            session: 数据库会话
            params: 搜索参数

        Returns:
            Tuple[记录列表, 总数, 应用的过滤条件]
        """
        # 构建基础查询
        query = select(DNSRecord)

        # 默认不包含已删除的记录
        query = query.where(DNSRecord.status != "deleted")

        # 记录应用的过滤条件
        filters_applied = {}

        # 全文搜索
        if params.q:
            query = query.where(
                or_(
                    DNSRecord.hostname.contains(params.q),
                    DNSRecord.ip_address.contains(params.q),
                    DNSRecord.description.contains(params.q)
                )
            )
            filters_applied["q"] = params.q

        # Zone 精确匹配
        if params.zone:
            query = query.where(DNSRecord.zone == params.zone)
            filters_applied["zone"] = params.zone

        # 主机名模糊匹配
        if params.hostname:
            query = query.where(DNSRecord.hostname.contains(params.hostname))
            filters_applied["hostname"] = params.hostname

        # IP 地址模糊匹配
        if params.ip:
            query = query.where(DNSRecord.ip_address.contains(params.ip))
            filters_applied["ip"] = params.ip

        # 记录类型精确匹配
        if params.record_type:
            query = query.where(DNSRecord.record_type == params.record_type)
            filters_applied["record_type"] = params.record_type

        # 状态精确匹配
        if params.status:
            query = query.where(DNSRecord.status == params.status)
            filters_applied["status"] = params.status

        # 时间范围过滤
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

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total = session.exec(count_query).one()

        # 应用排序
        order_column = getattr(DNSRecord, params.sort_by)
        if params.order == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # 应用分页
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        # 执行查询
        records = session.exec(query).all()

        return records, total, filters_applied
```

### 3. API 路由（app/api/records.py）
```python
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database import get_session
from app.services.dns_service import DNSService
from app.schemas.dns_record import DNSRecordSearchParams, DNSRecordSearchResponse
import math

router = APIRouter(prefix="/api/records", tags=["DNS Records"])

@router.get("/search", response_model=DNSRecordSearchResponse)
async def search_records(
    params: DNSRecordSearchParams = Depends(),
    session: Session = Depends(get_session)
):
    """
    搜索 DNS 记录

    支持多种搜索和过滤条件：
    - 全文搜索（q）
    - Zone 过滤
    - 主机名模糊匹配
    - IP 地址模糊匹配
    - 记录类型过滤
    - 状态过滤
    - 时间范围过滤
    """
    records, total, filters_applied = DNSService.search_records(session, params)

    pages = math.ceil(total / params.page_size) if total > 0 else 0

    return {
        "success": True,
        "data": records,
        "pagination": {
            "total": total,
            "page": params.page,
            "page_size": params.page_size,
            "pages": pages
        },
        "filters_applied": filters_applied
    }
```

### 4. 数据库索引优化（app/models/dns_record.py）
```python
from sqlmodel import SQLModel, Field, Index
from datetime import datetime

class DNSRecord(SQLModel, table=True):
    __tablename__ = "dns_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    zone: str = Field(index=True)  # 添加索引
    hostname: str = Field(index=True)  # 添加索引
    ip_address: str = Field(index=True)  # 添加索引
    record_type: str = Field(default="A", index=True)  # 添加索引
    description: Optional[str] = None
    status: str = Field(default="active", index=True)  # 添加索引
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_zone_hostname", "zone", "hostname"),  # 复合索引
        Index("idx_status_created", "status", "created_at"),  # 复合索引
    )
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要 DNSRecord 模型)
- **后置依赖**:
  - Story-015 (Web 搜索界面需要调用此 API)

## 测试用例

### 测试场景 1: 全文搜索
```python
def test_full_text_search():
    response = client.get("/api/records/search?q=app")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "app" in str(data["data"]).lower()
```

### 测试场景 2: Zone 过滤
```python
def test_filter_by_zone():
    response = client.get("/api/records/search?zone=seadee.com.cn")
    assert response.status_code == 200
    data = response.json()
    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"
```

### 测试场景 3: 多条件组合搜索
```python
def test_combined_filters():
    response = client.get(
        "/api/records/search?zone=seadee.com.cn&status=active&record_type=A"
    )
    assert response.status_code == 200
    data = response.json()
    assert "zone" in data["filters_applied"]
    assert "status" in data["filters_applied"]
    assert "record_type" in data["filters_applied"]
```

### 测试场景 4: 时间范围过滤
```python
def test_date_range_filter():
    from datetime import datetime, timedelta

    date_from = (datetime.utcnow() - timedelta(days=7)).isoformat()
    response = client.get(f"/api/records/search?created_after={date_from}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### 测试场景 5: 空结果
```python
def test_no_results():
    response = client.get("/api/records/search?q=nonexistent12345")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0
    assert data["pagination"]["total"] == 0
```

## 完成定义 (Definition of Done)
- [x] 搜索 API 端点已实现
- [x] 所有验收标准已满足
- [x] 支持多种搜索和过滤条件
- [x] 数据库索引已优化
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] 性能测试通过
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [SQLModel Advanced Filtering](https://sqlmodel.tiangolo.com/tutorial/where/)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [RESTful API Search Design](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Filtering-Sorting-and-Pagination/)

## 备注
- 考虑使用 Elasticsearch 进行全文搜索（在大规模数据场景下）
- 可以添加搜索建议功能（autocomplete）
- 可以添加搜索历史记录功能

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
