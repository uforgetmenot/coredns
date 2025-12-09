# Story-002: 数据库模型设计和迁移

## 基本信息
- **故事ID**: Story-002
- **所属Sprint**: Sprint 0
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Done ✅

## 用户故事
**As a** 开发者
**I want** 设计并实现完整的数据库模型
**So that** 可以持久化 DNS 记录、Zone 配置、操作日志等数据

## 背景描述
数据库是应用的核心，需要设计合理的数据模型来存储 DNS 记录、Zone 配置、Corefile 备份、操作日志和系统设置。使用 SQLModel 可以同时获得 Pydantic 的数据验证和 SQLAlchemy 的 ORM 能力。

## 验收标准

- [x] AC1:✅ 数据库连接模块已实现（`app/database.py`）
  - 配置 SQLite 数据库连接
  - 支持异步数据库操作
  - 实现数据库初始化函数
  - 实现表创建函数

- [x] AC2:✅ DNS 记录模型已实现（`app/models/dns_record.py`）
  - 包含所有必需字段：id, zone, hostname, ip_address, record_type, description, status, created_at, updated_at
  - 字段添加适当的索引
  - 字段添加验证规则
  - 包含示例数据（在文档字符串中）

- [x] AC3:✅ Zone 模型已实现（`app/models/zone.py`）
  - 包含字段：id, name, fallthrough, log_enabled, upstream_dns, status, created_at, updated_at
  - zone.name 字段添加唯一索引
  - 包含默认值配置

- [x] AC4:✅ Corefile 备份模型已实现（`app/models/backup.py`）
  - 包含字段：id, content, backup_reason, created_at
  - 支持存储大文本内容

- [x] AC5:✅ 操作日志模型已实现（`app/models/log.py`）
  - 包含字段：id, operation_type, resource_type, resource_id, details, user, ip_address, created_at
  - 添加复合索引以优化查询性能

- [x] AC6:✅ 系统设置模型已实现（`app/models/setting.py`）
  - 包含字段：id, key, value, description, updated_at
  - key 字段添加唯一索引

- [x] AC7:✅ 数据库初始化脚本已实现
  - 自动创建所有表
  - 插入默认系统设置
  - 插入示例数据（可选，用于开发测试）

- [x] AC8:✅ 数据库迁移机制已配置
  - 可以轻松重建数据库
  - 数据库文件存储在 `data/db/` 目录

## 技术实现要点

### 1. 数据库连接（app/database.py）
```python
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings
import os

# 确保数据库目录存在
os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "")), exist_ok=True)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}  # SQLite 特定配置
)

def create_db_and_tables():
    """创建所有表"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """获取数据库会话（依赖注入）"""
    with Session(engine) as session:
        yield session
```

### 2. DNS 记录模型（app/models/dns_record.py）
```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class DNSRecord(SQLModel, table=True):
    __tablename__ = "dns_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    zone: str = Field(index=True, max_length=255)
    hostname: str = Field(index=True, max_length=255)
    ip_address: str = Field(index=True, max_length=45)  # IPv6 最长 45 字符
    record_type: str = Field(default="A", max_length=10)
    description: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(default="active", max_length=20)  # active, inactive, deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "zone": "seadee.com.cn",
                "hostname": "app",
                "ip_address": "172.27.0.3",
                "record_type": "A",
                "description": "Application server",
                "status": "active"
            }
        }
```

### 3. Zone 模型（app/models/zone.py）
```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=255)
    fallthrough: bool = Field(default=True)
    log_enabled: bool = Field(default=True)
    upstream_dns: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4. 初始化脚本（app/models/__init__.py）
```python
from app.models.dns_record import DNSRecord
from app.models.zone import Zone
from app.models.backup import CorefileBackup
from app.models.log import OperationLog
from app.models.setting import SystemSetting

__all__ = [
    "DNSRecord",
    "Zone",
    "CorefileBackup",
    "OperationLog",
    "SystemSetting"
]
```

### 5. 数据库初始化（添加到 app/main.py）
```python
from app.database import create_db_and_tables

@app.on_event("startup")
async def on_startup():
    """应用启动时创建数据库表"""
    create_db_and_tables()
```

## 依赖关系
- **前置依赖**:
  - Story-001 (需要项目结构和 SQLModel 依赖)
- **后置依赖**:
  - Story-004 ~ Story-008 (所有 API 都需要数据模型)
  - Story-009 ~ Story-011 (Corefile 管理需要数据模型)
  - Story-016 ~ Story-020 (所有后续功能都需要数据模型)

## 测试用例

### 测试场景 1: 数据库表创建
```python
# tests/test_database.py
from app.database import create_db_and_tables, engine
from sqlmodel import SQLModel

def test_create_tables():
    """测试数据库表创建"""
    create_db_and_tables()

    # 验证表已创建
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "dns_records" in tables
    assert "zones" in tables
    assert "corefile_backups" in tables
    assert "operation_logs" in tables
    assert "system_settings" in tables
```

### 测试场景 2: DNS 记录 CRUD
```python
# tests/test_models.py
from app.models.dns_record import DNSRecord
from app.database import get_session

def test_create_dns_record():
    """测试创建 DNS 记录"""
    with next(get_session()) as session:
        record = DNSRecord(
            zone="test.com",
            hostname="www",
            ip_address="192.168.1.1",
            record_type="A"
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.id is not None
        assert record.status == "active"
        assert record.created_at is not None
```

### 测试场景 3: Zone 唯一性约束
```python
def test_zone_unique_constraint():
    """测试 Zone 名称唯一性约束"""
    with next(get_session()) as session:
        zone1 = Zone(name="example.com")
        session.add(zone1)
        session.commit()

        # 尝试创建同名 Zone，应该失败
        zone2 = Zone(name="example.com")
        session.add(zone2)

        with pytest.raises(IntegrityError):
            session.commit()
```

## 完成定义 (Definition of Done)
- [x] 代码已提交到 `feature/story-002` 分支 ✅
- [x] 所有验收标准已满足 ✅
- [x] 5 个模型类全部实现 ✅
- [x] 数据库初始化脚本可正常运行 ✅
- [x] 单元测试通过（覆盖率 ≥ 80%） ✅
- [x] 数据库文件成功创建在 `data/db/` 目录 ✅
- [x] 代码已合并到 `develop` 分支 ✅

## 参考资料
- [SQLModel 官方文档](https://sqlmodel.tiangolo.com/)
- [SQLite 数据类型](https://www.sqlite.org/datatype3.html)
- [SQLAlchemy 索引配置](https://docs.sqlalchemy.org/en/20/core/constraints.html)

## 备注
- SQLite 不支持某些高级特性（如 ALTER TABLE），如需修改表结构，建议删除数据库重建
- 考虑为 `dns_records` 表添加复合唯一索引：(zone, hostname, ip_address)
- `created_at` 和 `updated_at` 使用 UTC 时间

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
