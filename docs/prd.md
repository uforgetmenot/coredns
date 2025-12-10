# CoreDNS 管理工具 - 产品需求文档 (PRD)

## 1. 项目概述

### 1.1 项目名称
CoreDNS Management Tool (CoreDNS 管理工具)

### 1.2 项目背景
当前 CoreDNS 的 DNS 记录管理需要手动修改 Corefile 配置文件并重启容器，操作繁琐且容易出错。为了提高 DNS 记录管理效率，需要开发一个可视化的 Web 管理工具，支持对 DNS 记录的增删改查操作。

### 1.3 项目目标
- 提供友好的 Web 界面管理 CoreDNS 的 DNS 记录
- 支持 DNS 记录的查看、查询、添加、修改、删除操作
- 自动化 Corefile 配置文件的更新和 CoreDNS 容器的重载
- 保持操作日志和数据持久化
- 容器化部署，与 CoreDNS 协同工作

## 2. 技术架构

### 2.1 技术栈
- **后端框架**: FastAPI (高性能异步 Web 框架)
- **ORM 与数据模型**: SQLModel (结合 Pydantic 和 SQLAlchemy)
- **数据库**: SQLite3 (轻量级文件数据库)
- **依赖管理**: Poetry (Python 包管理工具)
- **模板引擎**: Jinja2 (渲染 HTML 模板)
- **前端框架**:
  - HTML5
  - TailwindCSS (实用优先的 CSS 框架)
  - DaisyUI (基于 Tailwind 的组件库)
- **配置管理**: python-dotenv (环境变量管理)
- **HTTP 客户端**: requests (用于与 CoreDNS 容器交互)
- **容器化**: Docker & Docker Compose

### 2.2 系统架构图
```
┌─────────────────────────────────────────────────────────┐
│                     用户浏览器                            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CoreDNS Manager (FastAPI)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Web Layer (Jinja2 + Tailwind + DaisyUI)        │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  API Layer (FastAPI Routes & Controllers)       │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Business Logic Layer (Services)                 │   │
│  │  - DNS Record CRUD                               │   │
│  │  - Corefile Parser & Generator                   │   │
│  │  - CoreDNS Reload Service                        │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  Data Layer (SQLModel + SQLite)                  │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌─────────────────────────┐
         │  Corefile (Volume)      │
         └──────────┬────────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  CoreDNS Container      │
         │  (registry.k8s.io/      │
         │   coredns/coredns)      │
         └─────────────────────────┘
```

### 2.3 数据流
1. 用户通过 Web 界面提交 DNS 记录操作请求
2. FastAPI 接收请求并验证数据
3. Service 层处理业务逻辑，更新数据库
4. 生成新的 Corefile 内容
5. 写入 Corefile 文件（通过共享 Volume）
6. 通知 CoreDNS 容器重载配置（通过 Docker API 或信号）
7. 返回操作结果给用户

## 3. 功能需求

### 3.1 DNS 记录管理

#### 3.1.1 查看 DNS 记录列表
- **功能描述**: 展示所有 DNS 记录，支持分页和排序
- **显示字段**:
  - Zone (域名区域，如 `seadee.com.cn`, `qsqcloud.com`)
  - Hostname (主机名，如 `app`, `www`)
  - Full Domain (完整域名，如 `app.seadee.com.cn`)
  - IP Address (IP 地址)
  - Record Type (记录类型，如 A, AAAA)
  - Status (状态: 启用/禁用)
  - Created At (创建时间)
  - Updated At (更新时间)
- **交互功能**:
  - 按 Zone 分组展示
  - 支持表格排序（按域名、IP、时间等）
  - 分页显示（默认 20 条/页）
  - 每行提供「编辑」「删除」操作按钮

#### 3.1.2 搜索/查询 DNS 记录
- **功能描述**: 根据条件快速查找 DNS 记录
- **搜索条件**:
  - 模糊搜索: 域名、主机名、IP 地址
  - 精确搜索: Zone、记录类型、状态
  - 组合搜索: 支持多条件组合
- **搜索结果**:
  - 实时搜索（输入时自动过滤）
  - 高亮显示匹配关键词
  - 显示匹配数量

#### 3.1.3 添加 DNS 记录
- **功能描述**: 创建新的 DNS 记录
- **表单字段**:
  - Zone (下拉选择或新建)
  - Hostname (文本输入)
  - IP Address (文本输入，支持 IPv4/IPv6 验证)
  - Record Type (下拉选择: A, AAAA, CNAME)
  - Description (可选，记录说明)
  - Status (启用/禁用，默认启用)
- **验证规则**:
  - Zone 不能为空
  - Hostname 符合域名规范
  - IP 地址格式验证
  - 同一 Zone 下的完整域名不能重复
- **操作流程**:
  1. 填写表单
  2. 前端验证
  3. 提交到后端
  4. 后端验证并保存到数据库
  5. 更新 Corefile
  6. 重载 CoreDNS
  7. 返回成功/失败消息

#### 3.1.4 修改 DNS 记录
- **功能描述**: 编辑已存在的 DNS 记录
- **可修改字段**: 与添加相同（除 Zone 外建议不可修改以避免混乱）
- **验证规则**: 与添加相同
- **操作流程**: 与添加类似
- **界面**: 弹窗或独立页面编辑

#### 3.1.5 删除 DNS 记录
- **功能描述**: 删除 DNS 记录
- **操作流程**:
  1. 点击删除按钮
  2. 弹出确认对话框（显示将要删除的记录详情）
  3. 确认后删除数据库记录
  4. 更新 Corefile
  5. 重载 CoreDNS
  6. 返回操作结果
- **软删除**: 建议使用软删除（标记为删除状态），保留历史记录

### 3.2 Zone 管理

#### 3.2.1 Zone 列表
- 显示所有 Zone 及其记录数量
- 支持 Zone 的启用/禁用
- 显示 Zone 的上游 DNS 配置

#### 3.2.2 Zone 配置
- Zone 名称
- Fallthrough 配置（是否启用 fallthrough）
- Log 配置（是否记录日志）
- 上游 DNS 服务器配置

### 3.3 Corefile 管理

#### 3.3.1 Corefile 预览
- 实时预览当前生成的 Corefile 内容
- 语法高亮显示
- 显示最后更新时间

#### 3.3.2 Corefile 备份
- 每次更新前自动备份 Corefile
- 显示备份历史列表
- 支持从备份恢复

#### 3.3.3 Corefile 验证
- 在应用前验证 Corefile 语法
- 显示验证错误信息

### 3.4 系统管理

#### 3.4.1 操作日志
- 记录所有 DNS 记录的操作（增删改）
- 记录操作用户、时间、操作类型、变更内容
- 支持日志查询和导出

#### 3.4.2 CoreDNS 状态监控
- 显示 CoreDNS 容器运行状态
- 显示最后重载时间
- 提供手动重载按钮
- 显示 CoreDNS 日志（最近 100 条）

#### 3.4.3 系统设置
- Corefile 路径配置
- CoreDNS 容器名称配置
- 数据库路径配置
- 日志保留天数配置

### 3.5 API 接口

#### 3.5.1 RESTful API 设计

```
# DNS 记录管理
GET    /api/records              # 获取记录列表（支持分页、搜索、过滤）
GET    /api/records/{id}         # 获取单条记录详情
POST   /api/records              # 创建记录
PUT    /api/records/{id}         # 更新记录
DELETE /api/records/{id}         # 删除记录

# Zone 管理
GET    /api/zones                # 获取 Zone 列表
GET    /api/zones/{name}         # 获取 Zone 详情
POST   /api/zones                # 创建 Zone
PUT    /api/zones/{name}         # 更新 Zone
DELETE /api/zones/{name}         # 删除 Zone

# Corefile 管理
GET    /api/corefile             # 获取当前 Corefile 内容
GET    /api/corefile/preview     # 预览将生成的 Corefile
POST   /api/corefile/validate    # 验证 Corefile
POST   /api/corefile/reload      # 重载 CoreDNS

# 备份管理
GET    /api/backups              # 获取备份列表
POST   /api/backups/restore/{id} # 恢复备份

# 日志管理
GET    /api/logs/operations      # 获取操作日志
GET    /api/logs/coredns         # 获取 CoreDNS 日志

# 系统管理
GET    /api/system/status        # 获取系统状态
GET    /api/system/settings      # 获取系统设置
PUT    /api/system/settings      # 更新系统设置
```

## 4. 数据模型设计

### 4.1 数据库表结构

#### 4.1.1 dns_records (DNS 记录表)
```python
class DNSRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    zone: str = Field(index=True)              # 域名区域
    hostname: str = Field(index=True)           # 主机名
    ip_address: str = Field(index=True)         # IP 地址
    record_type: str = Field(default="A")       # 记录类型 (A, AAAA, CNAME)
    description: Optional[str] = None           # 记录描述
    status: str = Field(default="active")       # 状态: active, inactive, deleted
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

#### 4.1.2 zones (Zone 配置表)
```python
class Zone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Zone 名称
    fallthrough: bool = Field(default=True)     # 是否启用 fallthrough
    log_enabled: bool = Field(default=True)     # 是否启用日志
    upstream_dns: Optional[str] = None          # 上游 DNS (如 "223.5.5.5")
    status: str = Field(default="active")       # 状态
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 4.1.3 corefile_backups (Corefile 备份表)
```python
class CorefileBackup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str                                # Corefile 内容
    backup_reason: str                          # 备份原因
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 4.1.4 operation_logs (操作日志表)
```python
class OperationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operation_type: str = Field(index=True)     # 操作类型: create, update, delete
    resource_type: str = Field(index=True)      # 资源类型: record, zone, corefile
    resource_id: Optional[int] = None           # 资源 ID
    details: str                                # 操作详情 (JSON)
    user: str = Field(default="admin")          # 操作用户
    ip_address: Optional[str] = None            # 操作 IP
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 4.1.5 system_settings (系统设置表)
```python
class SystemSetting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)   # 设置键
    value: str                                  # 设置值
    description: Optional[str] = None           # 设置说明
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.2 数据关系
- `dns_records.zone` 关联 `zones.name` (外键关系)
- 支持级联删除: 删除 Zone 时软删除所有相关记录

## 5. 界面设计

### 5.1 页面结构

#### 5.1.1 主布局
```
┌────────────────────────────────────────────────────────┐
│  Header (导航栏)                                        │
│  [CoreDNS Manager] [记录管理] [Zone管理] [日志] [设置] │
└────────────────────────────────────────────────────────┘
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │             Main Content Area                     │  │
│  │                                                   │  │
│  │                                                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└────────────────────────────────────────────────────────┘
│  Footer (状态栏)                                        │
│  CoreDNS: Running | 记录数: 45 | 最后更新: 2025-11-26  │
└────────────────────────────────────────────────────────┘
```

#### 5.1.2 DNS 记录列表页面
- 顶部搜索栏（搜索框 + 高级筛选按钮）
- 操作按钮区（「添加记录」按钮）
- Zone 标签页切换（All / Zone1 / Zone2 ...）
- 数据表格（使用 DaisyUI Table 组件）
- 分页控件

#### 5.1.3 添加/编辑记录表单
- 模态对话框或侧边抽屉形式
- 表单字段使用 DaisyUI 表单组件
- 实时验证提示
- 提交按钮和取消按钮

### 5.2 UI 组件库 (DaisyUI)
- **按钮**: btn, btn-primary, btn-secondary, btn-error
- **表格**: table, table-zebra, table-compact
- **表单**: form-control, input, select, textarea
- **模态框**: modal, modal-box
- **警告框**: alert, alert-success, alert-error
- **卡片**: card, card-body
- **徽章**: badge
- **加载器**: loading, loading-spinner

### 5.3 响应式设计
- 使用 Tailwind 的响应式类（sm:, md:, lg:, xl:）
- 移动端优先设计
- 支持桌面、平板、手机访问

## 6. CoreDNS 集成

### 6.1 Corefile 生成策略

#### 6.1.1 Corefile 模板结构
```
. {
    forward . <upstream-dns>
    log
    errors
}

# BEGIN MANAGED BLOCK <zone-name>
<zone-name> {
    hosts {
        <ip> <hostname>.<zone>
        <ip> <hostname>.<zone>
        ...
        fallthrough
    }
    log
    errors
}
# END MANAGED BLOCK <zone-name>
```

#### 6.1.2 生成规则
1. 保留默认的 `.` 根域配置
2. 按 Zone 分组生成配置块
3. 使用标记注释（`BEGIN/END MANAGED BLOCK`）标识管理范围
4. 按字母顺序排序记录（便于阅读和 diff）
5. 只生成状态为 `active` 的记录

### 6.2 CoreDNS 重载机制

#### 6.2.1 重载方式选择
1. **方式一: Docker Signal** (推荐)
   - 向 CoreDNS 容器发送 SIGUSR1 信号
   - 命令: `docker kill -s SIGUSR1 coredns`
   - 优点: 不重启容器，无服务中断

2. **方式二: Docker Restart**
   - 重启容器: `docker restart coredns`
   - 优点: 简单可靠
   - 缺点: 短暂服务中断

#### 6.2.2 重载流程
1. 验证新 Corefile 语法（可选）
2. 备份当前 Corefile
3. 写入新 Corefile
4. 发送重载信号
5. 验证 CoreDNS 状态
6. 记录操作日志

### 6.3 容器通信

#### 6.3.1 Volume 共享
- CoreDNS Manager 和 CoreDNS 共享 Corefile Volume
- 路径: `./data/Corefile:/Corefile`

#### 6.3.2 Docker Socket
- CoreDNS Manager 挂载 Docker Socket
- 路径: `/var/run/docker.sock:/var/run/docker.sock:ro`
- 用途: 发送重载信号、查询容器状态

## 7. 部署方案

### 7.1 Docker Compose 配置

#### 7.1.1 完整配置文件
```yaml
version: "3"

services:
  coredns:
    image: registry.k8s.io/coredns/coredns:v1.11.3
    container_name: coredns
    restart: always
    volumes:
      - ./data/Corefile:/Corefile
    ports:
      - "53:53/udp"
      - "53:53/tcp"
    networks:
      - coredns-net
    command: -conf /Corefile
    environment:
      - TZ=Asia/Shanghai
    sysctls:
      net.core.somaxconn: 4000
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  coredns-manager:
    build: .
    container_name: coredns-manager
    restart: always
    depends_on:
      - coredns
    volumes:
      - ./data/Corefile:/app/data/Corefile
      - ./data/db:/app/data/db
      - /var/run/docker.sock:/var/run/docker.sock:ro
    ports:
      - "8000:8000"
    networks:
      - coredns-net
    environment:
      - TZ=Asia/Shanghai
      - DATABASE_URL=sqlite:///app/data/db/coredns.db
      - COREFILE_PATH=/app/data/Corefile
      - COREDNS_CONTAINER_NAME=coredns
      - LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  coredns-net:
    driver: bridge

volumes:
  coredns-data:
```

### 7.2 项目目录结构
```
coredns/
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile                   # CoreDNS Manager 镜像
├── pyproject.toml              # Poetry 依赖配置
├── poetry.lock                 # 依赖锁定文件
├── .env                        # 环境变量配置
├── .dockerignore               # Docker 忽略文件
├── .gitignore                  # Git 忽略文件
├── README.md                   # 项目说明
├── docs/
│   └── prd.md                  # 本文档
├── data/                       # 数据目录（挂载到容器）
│   ├── Corefile                # CoreDNS 配置文件
│   └── db/                     # SQLite 数据库
│       └── coredns.db
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── dns_record.py
│   │   ├── zone.py
│   │   ├── backup.py
│   │   └── log.py
│   ├── schemas/                # Pydantic 模型（API 请求/响应）
│   │   ├── __init__.py
│   │   ├── dns_record.py
│   │   └── zone.py
│   ├── api/                    # API 路由
│   │   ├── __init__.py
│   │   ├── records.py
│   │   ├── zones.py
│   │   ├── corefile.py
│   │   └── system.py
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── dns_service.py
│   │   ├── corefile_service.py
│   │   ├── backup_service.py
│   │   └── docker_service.py
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── logger.py
│   ├── templates/              # Jinja2 模板
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── records.html
│   │   ├── zones.html
│   │   └── logs.html
│   └── static/                 # 静态文件
│       ├── css/
│       │   └── custom.css
│       └── js/
│           └── app.js
└── tests/                      # 测试文件
    ├── __init__.py
    ├── test_api.py
    └── test_services.py
```

### 7.3 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Poetry
RUN pip install poetry

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖（不创建虚拟环境）
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.4 环境变量配置 (.env)
```env
# Database
DATABASE_URL=sqlite:///app/data/db/coredns.db

# CoreDNS
COREFILE_PATH=/app/data/Corefile
COREDNS_CONTAINER_NAME=coredns

# Application
LOG_LEVEL=INFO
DEBUG=False
TIMEZONE=Asia/Shanghai

# Security (可选，用于未来扩展)
# SECRET_KEY=your-secret-key
# ALLOWED_HOSTS=*
```

## 8. 依赖管理 (Poetry)

### 8.1 pyproject.toml
```toml
[tool.poetry]
name = "coredns-manager"
version = "1.0.0"
description = "CoreDNS Management Tool"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlmodel = "^0.0.14"
python-dotenv = "^1.0.0"
jinja2 = "^3.1.2"
requests = "^2.31.0"
docker = "^7.0.0"
aiosqlite = "^0.19.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-asyncio = "^0.21.1"
black = "^23.11.0"
flake8 = "^6.1.0"
mypy = "^1.7.1"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## 9. 安全考虑

### 9.1 访问控制
- 建议添加基本的 HTTP 认证（可选功能）
- 限制 Docker Socket 的只读访问
- 环境变量不包含敏感信息

### 9.2 输入验证
- 所有用户输入必须验证（IP 地址、域名格式）
- 防止 SQL 注入（使用 SQLModel ORM）
- 防止 XSS 攻击（Jinja2 自动转义）

### 9.3 操作审计
- 所有修改操作记录日志
- 保留 Corefile 历史备份
- 记录操作用户和 IP

## 10. 错误处理

### 10.1 错误类型
- 数据验证错误（400 Bad Request）
- 资源不存在错误（404 Not Found）
- CoreDNS 重载失败（500 Internal Server Error）
- 数据库操作失败（500 Internal Server Error）

### 10.2 错误响应格式
```json
{
  "error": true,
  "message": "错误描述",
  "detail": "详细错误信息",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

### 10.3 回滚机制
- 操作失败时自动恢复 Corefile 备份
- 数据库事务回滚

## 11. 性能优化

### 11.1 数据库优化
- 为常用查询字段添加索引
- 使用连接池
- 定期清理过期日志

### 11.2 前端优化
- 使用 CDN 加载 TailwindCSS 和 DaisyUI
- 静态资源缓存
- 懒加载大型列表

### 11.3 缓存策略
- 缓存 Corefile 内容（减少文件 I/O）
- 缓存 Zone 列表（减少数据库查询）

## 12. 测试策略

### 12.1 单元测试
- 测试 Corefile 生成逻辑
- 测试数据验证函数
- 测试 CRUD 操作

### 12.2 集成测试
- 测试 API 端点
- 测试 CoreDNS 重载流程
- 测试备份恢复功能

### 12.3 端到端测试
- 测试完整的用户操作流程
- 测试错误处理和回滚

## 13. 文档要求

### 13.1 用户文档
- 快速开始指南
- 功能使用说明
- 常见问题 FAQ

### 13.2 开发文档
- 架构设计文档
- API 接口文档
- 数据库设计文档
- 部署指南

### 13.3 运维文档
- 安装部署步骤
- 配置说明
- 故障排查指南
- 备份恢复流程

## 14. 里程碑计划

### Phase 1: 核心功能 (MVP)
- [ ] 数据库模型设计和初始化
- [ ] DNS 记录 CRUD API
- [ ] Corefile 生成和更新
- [ ] CoreDNS 重载集成
- [ ] 基础 Web 界面（列表、添加、编辑、删除）

### Phase 2: 增强功能
- [ ] 搜索和过滤功能
- [ ] Zone 管理功能
- [ ] 操作日志记录
- [ ] Corefile 备份和恢复

### Phase 3: 系统完善
- [ ] 系统监控和状态展示
- [ ] 错误处理和用户提示优化
- [ ] 响应式界面优化
- [ ] 单元测试和集成测试

### Phase 4: 高级功能（可选）
- [ ] 用户认证和权限管理
- [ ] 批量导入/导出功能
- [ ] API 访问令牌
- [ ] 邮件/Webhook 通知

## 15. 依赖服务

### 15.1 外部依赖
- Docker Engine (v20.10+)
- Docker Compose (v2.0+)
- CoreDNS (v1.11.3)

### 15.2 Python 依赖
- Python 3.11+
- FastAPI 0.104+
- SQLModel 0.0.14+
- 其他依赖见 pyproject.toml

## 16. 运维监控

### 16.1 健康检查
- FastAPI 健康检查端点: `/health`
- CoreDNS 容器状态检查
- 数据库连接检查

### 16.2 日志管理
- 应用日志: 使用 Python logging
- 容器日志: Docker json-file driver
- 日志轮转: 10MB/文件，保留 3 个文件

### 16.3 告警机制（可选）
- CoreDNS 重载失败告警
- 数据库操作失败告警
- 系统资源告警

## 17. 未来扩展

### 17.1 功能扩展
- 支持更多 DNS 记录类型（MX, TXT, SRV 等）
- 支持多 CoreDNS 实例管理
- DNS 查询统计和分析
- 自定义 DNS 规则和插件配置

### 17.2 技术扩展
- 支持其他数据库（PostgreSQL, MySQL）
- 支持 Redis 缓存
- 支持 Kubernetes 部署
- 提供 CLI 工具

## 18. 参考资料

- CoreDNS 官方文档: https://coredns.io/manual/toc/
- FastAPI 文档: https://fastapi.tiangolo.com/
- SQLModel 文档: https://sqlmodel.tiangolo.com/
- TailwindCSS 文档: https://tailwindcss.com/docs
- DaisyUI 文档: https://daisyui.com/components/

---

**文档版本**: v1.0
**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**文档状态**: 草稿
