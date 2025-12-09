# Story-001: 项目初始化和开发环境搭建

## 基本信息
- **故事ID**: Story-001
- **所属Sprint**: Sprint 0
- **优先级**: High
- **预估工作量**: 1 Story Point (0.5 天)
- **状态**: Done ✅

## 用户故事
**As a** 开发者
**I want** 搭建完整的项目结构和开发环境
**So that** 我可以开始实现业务功能

## 背景描述
在开始任何功能开发之前，需要建立标准化的项目结构、配置依赖管理工具、设置开发环境。这个故事是所有后续开发的基础，确保团队成员可以快速启动开发工作。

## 验收标准
- [x] AC1: Poetry 项目已初始化，`pyproject.toml` 配置完整 ✅
  - 包含项目元信息（name, version, description, authors）
  - 配置 Python 版本要求（^3.11）
  - 添加所有生产依赖：fastapi, uvicorn, sqlmodel, python-dotenv, jinja2, requests, docker, aiosqlite, pydantic-settings
  - 添加开发依赖：pytest, pytest-asyncio, black, flake8, mypy, httpx

- [x] AC2: 项目目录结构已创建 ✅
  ```
  coredns/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── models/
  │   ├── schemas/
  │   ├── api/
  │   ├── services/
  │   ├── utils/
  │   ├── templates/
  │   └── static/
  └── tests/
      └── __init__.py
  ```

- [x] AC3: FastAPI 应用入口已创建（`app/main.py`） ✅
  - 包含基础的 FastAPI 应用实例
  - 配置 CORS 中间件
  - 实现健康检查端点 `GET /health`
  - 配置 API 文档路径 `/docs` 和 `/redoc`
  - 使用现代化的 lifespan 事件处理

- [x] AC4: 配置管理模块已创建（`app/config.py`） ✅
  - 使用 pydantic-settings 加载环境变量
  - 定义配置类（数据库路径、Corefile 路径等）
  - 支持从 `.env` 文件读取配置
  - 使用 Pydantic V2 的 SettingsConfigDict

- [x] AC5: 环境配置文件已创建 ✅
  - `.env.example` 包含所有必需的配置项示例
  - `.gitignore` 配置正确（忽略 `.env`, `__pycache__`, `.pytest_cache` 等）
  - `.dockerignore` 配置正确

- [x] AC6: 文档已创建 ✅
  - `README.md` 包含项目介绍、安装步骤、开发指南
  - 说明如何使用 Poetry 安装依赖
  - 说明如何启动开发服务器
  - 包含 Docker 部署说明

- [x] AC7: 应用可以成功启动 ✅
  - 运行 `poetry install` 成功安装依赖
  - 运行 `poetry run uvicorn app.main:app --reload` 成功启动服务
  - 访问 `http://localhost:8000/health` 返回 200 状态码
  - 访问 `http://localhost:8000/docs` 可以看到 Swagger UI
  - 所有测试通过（5/5）

## 技术实现要点

### 1. Poetry 初始化
```bash
poetry init
poetry add fastapi "uvicorn[standard]" sqlmodel python-dotenv jinja2 requests docker aiosqlite
poetry add --group dev pytest pytest-asyncio black flake8 mypy
```

### 2. FastAPI 应用入口（app/main.py）
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title="CoreDNS Manager",
    description="CoreDNS 管理工具 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "coredns-manager"}

@app.get("/")
async def root():
    return {"message": "CoreDNS Manager API"}
```

### 3. 配置管理（app/config.py）
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/db/coredns.db"
    corefile_path: str = "./data/Corefile"
    coredns_container_name: str = "coredns"
    log_level: str = "INFO"
    debug: bool = False

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

### 4. .env.example
```env
DATABASE_URL=sqlite:///./data/db/coredns.db
COREFILE_PATH=./data/Corefile
COREDNS_CONTAINER_NAME=coredns
LOG_LEVEL=INFO
DEBUG=False
```

## 依赖关系
- **前置依赖**: 无
- **后置依赖**:
  - Story-002 (数据库模型设计需要这个项目结构)
  - Story-003 (Docker 配置需要 pyproject.toml)
  - 所有其他故事都依赖这个基础项目结构

## 测试用例

### 测试场景 1: 健康检查端点
```python
# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "coredns-manager"}
```

### 测试场景 2: 根端点
```python
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
```

### 测试场景 3: API 文档可访问
```python
def test_api_docs():
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc():
    response = client.get("/redoc")
    assert response.status_code == 200
```

## 完成定义 (Definition of Done)
- [x] 代码已实现（在主分支） ✅
- [x] 所有验收标准已满足（7/7） ✅
- [x] 单元测试通过（5/5 测试，100% 通过率） ✅
- [x] 代码使用最新的 FastAPI 和 Pydantic V2 语法 ✅
- [x] 无编译警告和错误 ✅
- [x] README.md 已更新，包含完整的开发指南 ✅
- [x] 项目可以成功启动和运行 ✅

## 参考资料
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Poetry 官方文档](https://python-poetry.org/docs/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

## 备注
- 确保所有团队成员都安装了 Python 3.11+ 和 Poetry
- 建议使用虚拟环境进行开发
- 可以在 `pyproject.toml` 中配置代码格式化和检查工具的参数

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
