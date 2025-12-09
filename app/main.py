"""
CoreDNS Manager - FastAPI 应用入口
提供 DNS 记录管理的 REST API
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app import models  # noqa: F401
from app.api import corefile, coredns, records
from app.config import settings
from app.database import create_db_and_tables
from app.routes import pages


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """应用生命周期管理"""
    # 启动
    print("🚀 CoreDNS Manager starting...")
    print(f"📊 Debug mode: {settings.debug}")
    print(f"📁 Database: {settings.database_url}")
    print(f"📄 Corefile: {settings.corefile_path}")

    # 创建数据库表
    print("📦 Creating database tables...")
    create_db_and_tables()
    print("✅ Database initialized successfully")

    yield

    # 关闭
    print("👋 CoreDNS Manager shutting down...")


# 创建 FastAPI 应用实例
application = FastAPI(
    title="CoreDNS Manager",
    description="CoreDNS 管理工具 API - 提供 DNS 记录的增删改查功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS 中间件
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
application.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="coredns_session",
)

static_dir = Path(__file__).resolve().parent / "static"
application.mount("/static", StaticFiles(directory=static_dir), name="static")

# 注册 API 路由
application.include_router(records.router)
application.include_router(corefile.router)
application.include_router(coredns.router)
application.include_router(pages.router)


@application.get("/health", tags=["System"])
async def health_check():
    """
    健康检查端点
    用于监控服务状态
    """
    return {
        "status": "healthy",
        "service": "coredns-manager",
        "version": "1.0.0",
    }


@application.get("/", include_in_schema=False)
async def root():
    """Redirect base URL to dashboard shell"""

    return RedirectResponse(url="/dashboard", status_code=307)


# 向后兼容的别名
app = application
