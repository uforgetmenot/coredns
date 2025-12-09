"""
配置管理模块
使用 pydantic-settings 管理应用配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""

    # 数据库配置
    database_url: str = "sqlite:///./data/db/coredns.db"

    # CoreDNS 配置
    corefile_path: str = "./data/Corefile"
    corefile_backup_dir: str = "./data/backups"
    coredns_container_name: str = "coredns"
    auto_reload_on_generate: bool = True
    max_corefile_backups: int = 30
    max_backup_size_bytes: int = 5 * 1024 * 1024  # 5 MB
    coredns_reload_method: str = "docker"  # docker | process

    # 上级 DNS 默认配置
    upstream_primary_dns_default: str = "8.8.8.8"
    upstream_secondary_dns_default: str | None = "8.8.4.4"

    # 应用配置
    log_level: str = "INFO"
    debug: bool = False
    secret_key: str = "change-me"  # 用于会话与 CSRF 等
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # OAuth2 外部认证配置
    oauth2_enabled: bool = True  # 是否启用外部 OAuth2 认证
    oauth2_server_url: str = "http://core.seadee.com.cn:8099"  # OAuth2 认证服务器地址
    oauth2_token_endpoint: str = "/auth/token"  # Token 获取端点
    oauth2_userinfo_endpoint: str = "/auth/me"  # 用户信息端点
    oauth2_refresh_endpoint: str = "/auth/refresh"  # Token 刷新端点
    oauth2_token_refresh_interval: int = 3600  # Token 刷新间隔（秒）

    # 时区
    timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()
