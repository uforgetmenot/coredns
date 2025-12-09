"""Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def api_login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    API 登录端点

    使用用户名和密码进行认证，支持本地认证和 OAuth2 认证
    """
    try:
        username, user_info = auth_service.authenticate(
            username=request.username, password=request.password
        )

        return LoginResponse(
            success=True, message="Login successful", user=user_info
        )

    except HTTPException as e:
        return LoginResponse(
            success=False, message=e.detail or "Authentication failed", user=None
        )


@router.post("/logout")
async def api_logout(
    username: str, auth_service: AuthService = Depends(get_auth_service)
):
    """
    API 登出端点

    清除用户的认证信息和 Token
    """
    auth_service.logout(username)
    return {"success": True, "message": "Logout successful"}


@router.post("/refresh/{username}")
async def api_refresh_token(
    username: str, auth_service: AuthService = Depends(get_auth_service)
):
    """
    手动刷新指定用户的 Access Token

    Args:
        username: 要刷新 Token 的用户名
    """
    success = auth_service.refresh_token(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
        )

    return {"success": True, "message": "Token refreshed successfully"}
