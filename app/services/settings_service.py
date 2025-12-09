"""Settings service for managing system configuration"""

import logging
from typing import Optional
from sqlmodel import Session, select

from app.config import settings
from app.models.setting import SystemSetting

logger = logging.getLogger(__name__)


class SettingsService:
    """系统设置服务"""

    # 设置键常量
    KEY_PRIMARY_DNS = "upstream_primary_dns"
    KEY_SECONDARY_DNS = "upstream_secondary_dns"

    # 默认值
    DEFAULT_PRIMARY_DNS = settings.upstream_primary_dns_default
    DEFAULT_SECONDARY_DNS = settings.upstream_secondary_dns_default

    def __init__(self, session: Session):
        self.session = session

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取设置值"""
        statement = select(SystemSetting).where(SystemSetting.key == key)
        setting = self.session.exec(statement).first()
        return setting.value if setting else default

    def set_setting(
        self, key: str, value: str, description: Optional[str] = None
    ) -> SystemSetting:
        """设置或更新设置值"""
        statement = select(SystemSetting).where(SystemSetting.key == key)
        setting = self.session.exec(statement).first()

        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSetting(key=key, value=value, description=description)
            self.session.add(setting)

        self.session.commit()
        self.session.refresh(setting)
        logger.info(f"Setting updated: {key} = {value}")
        return setting

    def get_upstream_dns(self) -> tuple[str, Optional[str]]:
        """获取上级 DNS 配置"""
        primary = self.get_setting(self.KEY_PRIMARY_DNS, self.DEFAULT_PRIMARY_DNS)
        secondary = self.get_setting(self.KEY_SECONDARY_DNS)
        # 返回已保存的值或默认值（primary 会回退到默认值）；若 secondary 未配置则返回 None
        return primary, secondary if secondary else None

    def set_upstream_dns(
        self, primary_dns: str, secondary_dns: Optional[str] = None
    ) -> tuple[str, Optional[str]]:
        """设置上级 DNS 配置"""
        self.set_setting(
            self.KEY_PRIMARY_DNS,
            primary_dns,
            "Primary upstream DNS server",
        )

        if secondary_dns:
            self.set_setting(
                self.KEY_SECONDARY_DNS,
                secondary_dns,
                "Secondary upstream DNS server",
            )
        else:
            # 如果没有提供备用 DNS，删除或清空该设置
            statement = select(SystemSetting).where(
                SystemSetting.key == self.KEY_SECONDARY_DNS
            )
            setting = self.session.exec(statement).first()
            if setting:
                self.session.delete(setting)
                self.session.commit()

        logger.info(f"Upstream DNS updated: {primary_dns}, {secondary_dns}")
        return primary_dns, secondary_dns

    def initialize_default_settings(self) -> None:
        """初始化默认设置（如果不存在）"""
        primary = self.get_setting(self.KEY_PRIMARY_DNS)
        if not primary:
            self.set_setting(
                self.KEY_PRIMARY_DNS,
                self.DEFAULT_PRIMARY_DNS,
                "Primary upstream DNS server",
            )

        secondary = self.get_setting(self.KEY_SECONDARY_DNS)
        if not secondary and self.DEFAULT_SECONDARY_DNS:
            self.set_setting(
                self.KEY_SECONDARY_DNS,
                self.DEFAULT_SECONDARY_DNS,
                "Secondary upstream DNS server",
            )
