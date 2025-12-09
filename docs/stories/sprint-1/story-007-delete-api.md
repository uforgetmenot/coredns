# Story-007: DNS 记录删除 API

## 基本信息
- **故事ID**: Story-007
- **所属Sprint**: Sprint 1
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 通过 API 删除 DNS 记录
**So that** 可以移除不再需要的域名解析配置

## 背景描述
DNS 记录删除需要支持软删除和硬删除两种方式。软删除将记录标记为已删除但保留在数据库中，硬删除则物理删除记录。删除成功后需要触发 Corefile 重新生成。

## 验收标准

- [x] AC1: DELETE `/api/records/{id}` 端点已实现
  - 接收记录 ID 作为路径参数
  - 默认执行软删除（将 status 设置为 deleted）
  - 返回 200 状态码和删除确认信息

- [x] AC2: 支持删除模式选择
  - `mode`: 查询参数，可选值 soft/hard
  - `soft`: 软删除，设置 status = deleted（默认）
  - `hard`: 硬删除，从数据库物理删除记录

- [x] AC3: 软删除逻辑
  - 将记录的 status 设置为 deleted
  - 保留所有其他字段不变
  - 更新 updated_at 时间戳
  - 软删除的记录不会出现在列表查询中

- [x] AC4: 硬删除逻辑
  - 从数据库中物理删除记录
  - 删除前检查记录是否存在
  - 删除操作不可逆

- [x] AC5: 响应格式符合规范
  ```json
  {
    "success": true,
    "message": "DNS record deleted successfully",
    "mode": "soft"
  }
  ```

- [x] AC6: 错误处理完善
  - 404 Not Found: 记录不存在
  - 400 Bad Request: 记录已被删除（软删除时）
  - 500 Internal Server Error: 服务器错误

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试软删除
  - 测试硬删除
  - 测试记录不存在
  - 测试重复删除
  - 测试删除模式参数

## 技术实现要点

### 1. Pydantic 响应模型（app/schemas/dns_record.py）
```python
from pydantic import BaseModel

class DNSRecordDeleteResponse(BaseModel):
    success: bool = True
    message: str
    mode: str  # soft 或 hard
```

### 2. Service 层（app/services/dns_service.py）
```python
from sqlmodel import Session
from app.models.dns_record import DNSRecord
from fastapi import HTTPException
from datetime import datetime

class DNSService:
    @staticmethod
    def delete_record(
        session: Session,
        record_id: int,
        mode: str = "soft"
    ) -> dict:
        """
        删除 DNS 记录

        Args:
            session: 数据库会话
            record_id: 记录 ID
            mode: 删除模式，soft（软删除）或 hard（硬删除）

        Returns:
            dict: 删除结果信息
        """
        # 查找记录
        db_record = session.get(DNSRecord, record_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="DNS record not found")

        if mode == "soft":
            # 软删除
            if db_record.status == "deleted":
                raise HTTPException(
                    status_code=400,
                    detail="Record is already deleted"
                )

            db_record.status = "deleted"
            db_record.updated_at = datetime.utcnow()
            session.add(db_record)
            session.commit()

            return {
                "message": "DNS record deleted successfully (soft delete)",
                "mode": "soft"
            }

        elif mode == "hard":
            # 硬删除
            session.delete(db_record)
            session.commit()

            return {
                "message": "DNS record permanently deleted (hard delete)",
                "mode": "hard"
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid delete mode. Use 'soft' or 'hard'"
            )
```

### 3. API 路由（app/api/records.py）
```python
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.database import get_session
from app.services.dns_service import DNSService
from app.schemas.dns_record import DNSRecordDeleteResponse

router = APIRouter(prefix="/api/records", tags=["DNS Records"])

@router.delete("/{record_id}", response_model=DNSRecordDeleteResponse)
async def delete_record(
    record_id: int,
    mode: str = Query(
        "soft",
        regex="^(soft|hard)$",
        description="删除模式：soft（软删除）或 hard（硬删除）"
    ),
    session: Session = Depends(get_session)
):
    """
    删除 DNS 记录

    - **soft**: 软删除，将记录标记为已删除（默认）
    - **hard**: 硬删除，物理删除记录（不可恢复）
    """
    result = DNSService.delete_record(session, record_id, mode)
    return {
        "success": True,
        **result
    }
```

### 4. 列表 API 更新（排除已删除记录）
```python
# 在 list_records 方法中默认过滤掉已删除的记录
def list_records(
    session: Session,
    page: int = 1,
    page_size: int = 20,
    zone: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    include_deleted: bool = False  # 新增参数
):
    query = select(DNSRecord)

    # 默认不包含已删除的记录
    if not include_deleted:
        query = query.where(DNSRecord.status != "deleted")

    # 其他过滤逻辑...
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要 DNSRecord 模型)
- **后置依赖**:
  - Story-009 (Corefile 生成需要在记录删除后触发)
  - Story-013 (Web 列表页面需要调用此 API)

## 测试用例

### 测试场景 1: 成功软删除
```python
def test_soft_delete_success():
    # 创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "delete-test",
        "ip_address": "172.27.0.10"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 软删除
    response = client.delete(f"/api/records/{record_id}?mode=soft")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["mode"] == "soft"

    # 验证记录仍在数据库中但状态为 deleted
    get_response = client.get(f"/api/records/{record_id}")
    # 应该返回 404 或标记为 deleted
```

### 测试场景 2: 成功硬删除
```python
def test_hard_delete_success():
    # 创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "hard-delete",
        "ip_address": "172.27.0.11"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 硬删除
    response = client.delete(f"/api/records/{record_id}?mode=hard")
    assert response.status_code == 200
    result = response.json()
    assert result["mode"] == "hard"

    # 验证记录已从数据库中删除
    get_response = client.get(f"/api/records/{record_id}")
    assert get_response.status_code == 404
```

### 测试场景 3: 删除不存在的记录
```python
def test_delete_nonexistent_record():
    response = client.delete("/api/records/99999")
    assert response.status_code == 404
```

### 测试场景 4: 重复软删除
```python
def test_duplicate_soft_delete():
    # 创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "duplicate-delete",
        "ip_address": "172.27.0.12"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 第一次软删除
    response1 = client.delete(f"/api/records/{record_id}?mode=soft")
    assert response1.status_code == 200

    # 第二次软删除
    response2 = client.delete(f"/api/records/{record_id}?mode=soft")
    assert response2.status_code == 400  # 已经被删除
```

### 测试场景 5: 无效的删除模式
```python
def test_invalid_delete_mode():
    # 创建记录
    create_data = {
        "zone": "seadee.com.cn",
        "hostname": "invalid-mode",
        "ip_address": "172.27.0.13"
    }
    create_response = client.post("/api/records", json=create_data)
    record_id = create_response.json()["data"]["id"]

    # 使用无效模式
    response = client.delete(f"/api/records/{record_id}?mode=invalid")
    assert response.status_code == 422  # Validation error
```

## 完成定义 (Definition of Done)
- [x] DELETE 端点已实现
- [x] 所有验收标准已满足
- [x] 软删除和硬删除逻辑已实现
- [x] 列表 API 默认排除已删除记录
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [Soft Delete Pattern](https://www.culttt.com/2014/04/30/soft-deletes)
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [RESTful API Delete Methods](https://restfulapi.net/http-methods/#delete)

## 备注
- 建议默认使用软删除，以保留历史记录用于审计
- 硬删除应该有额外的权限控制（在后续的认证授权功能中实现）
- 可以考虑添加批量删除功能（在后续版本中实现）
- 软删除的记录可以通过特殊 API 恢复（可选功能，不在本 MVP 范围内）

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
