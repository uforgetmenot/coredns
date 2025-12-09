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

    # 应用配置
    log_level: str = "INFO"
    debug: bool = False
    secret_key: str = "change-me"  # 用于会话与 CSRF 等
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # 时区
    timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()
