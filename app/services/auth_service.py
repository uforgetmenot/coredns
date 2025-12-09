"""Simple authentication helpers for admin login"""

from __future__ import annotations

from hmac import compare_digest

from fastapi import HTTPException, status

from app.config import settings


class AuthService:
    """Lightweight auth service backed by static admin credentials"""

    def authenticate(self, username: str, password: str) -> str:
        """Validate username/password pair.

        Raises:
            HTTPException: when credentials are invalid
        Returns:
            str: the authenticated username
        """

        if self._is_valid(username, password):
            return username
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    def _is_valid(self, username: str, password: str) -> bool:
        return compare_digest(username, settings.admin_username) and compare_digest(
            password, settings.admin_password
        )
