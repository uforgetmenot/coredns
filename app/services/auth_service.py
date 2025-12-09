"""Authentication service with OAuth2 support"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from hmac import compare_digest

import requests
from fastapi import HTTPException, status

from app.config import settings
from app.schemas.auth import (
    OAuth2TokenRequest,
    OAuth2TokenResponse,
    OAuth2RefreshRequest,
    UserInfo,
)

logger = logging.getLogger(__name__)


class TokenStore:
    """简单的内存 Token 存储"""

    def __init__(self):
        self._tokens: dict[str, dict] = {}

    def save_token(self, username: str, access_token: str, refresh_token: str):
        """保存用户的 Token"""
        self._tokens[username] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "updated_at": datetime.now(),
        }

    def get_token(self, username: str) -> dict | None:
        """获取用户的 Token"""
        return self._tokens.get(username)

    def remove_token(self, username: str):
        """移除用户的 Token"""
        self._tokens.pop(username, None)

    def get_all_tokens(self) -> dict[str, dict]:
        """获取所有 Token（用于定期刷新）"""
        return self._tokens.copy()


class AuthService:
    """Authentication service supporting both local and OAuth2 modes"""

    def __init__(self):
        self.token_store = TokenStore()

    def authenticate(self, username: str, password: str) -> tuple[str, UserInfo]:
        """验证用户凭证并返回用户信息.

        Args:
            username: 用户名
            password: 密码

        Returns:
            tuple[str, UserInfo]: (用户名, 用户信息)

        Raises:
            HTTPException: 认证失败时抛出异常
        """
        if settings.oauth2_enabled:
            return self._authenticate_oauth2(username, password)
        else:
            return self._authenticate_local(username, password)

    def _authenticate_local(self, username: str, password: str) -> tuple[str, UserInfo]:
        """本地认证（原有逻辑）"""
        if self._is_valid_local(username, password):
            user_info = UserInfo(
                id=1,
                username=username,
                email=f"{username}@local",
                full_name=username,
                is_active=True,
                is_superuser=True,
                must_change_password=False,
            )
            return username, user_info
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    def _is_valid_local(self, username: str, password: str) -> bool:
        """验证本地用户凭证"""
        return compare_digest(username, settings.admin_username) and compare_digest(
            password, settings.admin_password
        )

    def _authenticate_oauth2(self, username: str, password: str) -> tuple[str, UserInfo]:
        """OAuth2 认证"""
        try:
            # 步骤 1: 使用密码模式获取 Token
            token_url = f"{settings.oauth2_server_url}{settings.oauth2_token_endpoint}"

            # OAuth2 标准使用 form-urlencoded 格式
            token_data = {
                "username": username,
                "password": password,
                "grant_type": "password"
            }

            logger.info(f"Authenticating user {username} via OAuth2: {token_url}")
            response = requests.post(
                token_url, data=token_data, timeout=10
            )

            if response.status_code != 200:
                logger.warning(
                    f"OAuth2 authentication failed for {username}: {response.status_code} {response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

            token_data = OAuth2TokenResponse(**response.json())

            # 步骤 2: 使用 Access Token 获取用户信息
            user_info = self._get_user_info(token_data.access_token)

            # 只允许 superuser 登录
            if not user_info.is_superuser:
                logger.warning(f"User {username} is not a superuser, access denied")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only superusers are allowed to login",
                )

            # 保存 Token 用于后续刷新
            self.token_store.save_token(
                username, token_data.access_token, token_data.refresh_token
            )

            logger.info(f"User {username} authenticated successfully via OAuth2")
            return username, user_info

        except requests.RequestException as e:
            logger.error(f"OAuth2 server connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OAuth2 authentication: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error",
            )

    def _get_user_info(self, access_token: str) -> UserInfo:
        """使用 Access Token 获取用户信息"""
        try:
            userinfo_url = (
                f"{settings.oauth2_server_url}{settings.oauth2_userinfo_endpoint}"
            )
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(userinfo_url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Failed to get user info: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to retrieve user information",
                )

            return UserInfo(**response.json())

        except requests.RequestException as e:
            logger.error(f"Error fetching user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User info service unavailable",
            )

    def refresh_token(self, username: str) -> bool:
        """刷新指定用户的 Access Token

        Args:
            username: 用户名

        Returns:
            bool: 刷新是否成功
        """
        if not settings.oauth2_enabled:
            return True  # 本地模式不需要刷新

        token_data = self.token_store.get_token(username)
        if not token_data:
            logger.warning(f"No token found for user {username}")
            return False

        try:
            refresh_url = (
                f"{settings.oauth2_server_url}{settings.oauth2_refresh_endpoint}"
            )

            # OAuth2 标准使用 form-urlencoded 格式
            refresh_data = {
                "refresh_token": token_data["refresh_token"]
            }

            logger.info(f"Refreshing token for user {username}")
            response = requests.post(
                refresh_url, data=refresh_data, timeout=10
            )

            if response.status_code != 200:
                logger.error(
                    f"Token refresh failed for {username}: {response.status_code}"
                )
                self.token_store.remove_token(username)
                return False

            new_token_data = OAuth2TokenResponse(**response.json())
            self.token_store.save_token(
                username, new_token_data.access_token, token_data["refresh_token"]
            )

            logger.info(f"Token refreshed successfully for user {username}")
            return True

        except Exception as e:
            logger.error(f"Error refreshing token for {username}: {e}")
            return False

    def refresh_all_tokens(self):
        """刷新所有用户的 Token（定期调用）"""
        if not settings.oauth2_enabled:
            return

        logger.info("Starting token refresh for all users")
        tokens = self.token_store.get_all_tokens()

        for username in tokens.keys():
            self.refresh_token(username)

    def logout(self, username: str):
        """用户登出，清除 Token"""
        self.token_store.remove_token(username)
        logger.info(f"User {username} logged out")


@lru_cache()
def get_auth_service() -> AuthService:
    """获取认证服务单例实例"""
    return AuthService()

