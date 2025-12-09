"""OAuth2 认证相关的 Pydantic schemas"""

from pydantic import BaseModel, Field


class OAuth2TokenRequest(BaseModel):
    """OAuth2 密码模式登录请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    grant_type: str = Field(default="password", description="授权类型")


class OAuth2TokenResponse(BaseModel):
    """OAuth2 Token 响应"""

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(..., description="令牌类型")
    expires_in: int | None = Field(None, description="过期时间(秒)")


class OAuth2RefreshRequest(BaseModel):
    """OAuth2 Token 刷新请求"""

    refresh_token: str = Field(..., description="刷新令牌")


class UserInfo(BaseModel):
    """OAuth2 用户信息"""

    id: int = Field(..., description="用户 ID")
    username: str = Field(..., description="用户名")
    email: str | None = Field(None, description="邮箱")
    full_name: str | None = Field(None, description="全名")
    is_active: bool = Field(True, description="是否激活")
    is_superuser: bool = Field(False, description="是否为超级用户")
    must_change_password: bool = Field(False, description="是否必须修改密码")


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    user: UserInfo | None = Field(None, description="用户信息")
