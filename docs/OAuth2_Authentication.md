# OAuth2 认证接入文档

## 概述

CoreDNS Manager 支持通过外部 OAuth2 认证服务进行集中认证。系统实现了 OAuth2 密码模式（Password Grant Type），支持用户登录认证、Token 自动刷新等功能。

## 功能特性

- ✅ OAuth2 密码模式认证
- ✅ 仅允许 superuser 登录
- ✅ 自动定期刷新 Access Token
- ✅ 支持本地认证和 OAuth2 认证切换
- ✅ 单例模式管理认证服务和 Token 存储

## 配置说明

### 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# OAuth2 外部认证配置
OAUTH2_ENABLED=True                                    # 是否启用 OAuth2 认证
OAUTH2_SERVER_URL=http://core.seadee.com.cn:8099     # OAuth2 服务器地址
OAUTH2_TOKEN_ENDPOINT=/auth/token                      # Token 获取端点
OAUTH2_USERINFO_ENDPOINT=/auth/me                      # 用户信息端点
OAUTH2_REFRESH_ENDPOINT=/auth/refresh                  # Token 刷新端点
OAUTH2_TOKEN_REFRESH_INTERVAL=3600                     # Token 刷新间隔（秒）
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `OAUTH2_ENABLED` | bool | True | 是否启用 OAuth2 认证，设为 False 则使用本地认证 |
| `OAUTH2_SERVER_URL` | string | http://core.seadee.com.cn:8099 | OAuth2 认证服务器的基础 URL |
| `OAUTH2_TOKEN_ENDPOINT` | string | /auth/token | 获取 Token 的 API 端点 |
| `OAUTH2_USERINFO_ENDPOINT` | string | /auth/me | 获取用户信息的 API 端点 |
| `OAUTH2_REFRESH_ENDPOINT` | string | /auth/refresh | 刷新 Token 的 API 端点 |
| `OAUTH2_TOKEN_REFRESH_INTERVAL` | int | 3600 | Token 自动刷新间隔（秒），默认 1 小时 |

## 认证流程

### 1. 用户登录

用户在登录页面输入用户名和密码后，系统执行以下步骤：

1. **发送认证请求**
   - 向 `{OAUTH2_SERVER_URL}{OAUTH2_TOKEN_ENDPOINT}` 发送 POST 请求
   - 使用 `application/x-www-form-urlencoded` 格式（OAuth2 标准）
   - 请求体：
     ```
     username=admin&password=Admin123&grant_type=password
     ```
   - 或使用表单数据：
     ```bash
     curl -X POST http://core.seadee.com.cn:8099/auth/token \
       -d "username=admin" \
       -d "password=Admin123" \
       -d "grant_type=password"
     ```

2. **接收 Token 响应**
   - 成功时收到 `access_token` 和 `refresh_token`
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

3. **获取用户信息**
   - 使用 `access_token` 向 `{OAUTH2_SERVER_URL}{OAUTH2_USERINFO_ENDPOINT}` 发送请求
   - 请求头：`Authorization: Bearer {access_token}`
   - 响应示例：
   ```json
   {
     "id": 1,
     "username": "admin",
     "email": "admin@example.com",
     "full_name": "系统管理员",
     "is_active": true,
     "is_superuser": true,
     "must_change_password": false
   }
   ```

4. **验证权限**
   - 检查 `is_superuser` 字段，只允许超级用户登录
   - 非超级用户将收到 403 Forbidden 错误

5. **保存 Token**
   - 将 `access_token` 和 `refresh_token` 保存到内存存储中
   - 将用户信息保存到 Session 中

### 2. Token 自动刷新

系统启动时会创建后台任务，定期刷新所有在线用户的 Token：

1. **定期执行**
   - 每隔 `OAUTH2_TOKEN_REFRESH_INTERVAL` 秒执行一次

2. **刷新流程**
   - 向 `{OAUTH2_SERVER_URL}{OAUTH2_REFRESH_ENDPOINT}` 发送 POST 请求
   - 使用 `application/x-www-form-urlencoded` 格式
   - 请求体：
     ```
     refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```
   - 或使用表单数据：
     ```bash
     curl -X POST http://core.seadee.com.cn:8099/auth/refresh \
       -d "refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
     ```

3. **更新 Token**
   - 收到新的 `access_token` 后更新内存存储
   - 如果刷新失败，清除该用户的 Token（用户需重新登录）

### 3. 用户登出

用户登出时：
1. 从内存中清除该用户的 Token
2. 清除 Session
3. 重定向到登录页面

## API 端点

### 1. POST `/api/auth/login`

API 登录端点

**请求体：**
```json
{
  "username": "admin",
  "password": "Admin123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "系统管理员",
    "is_active": true,
    "is_superuser": true,
    "must_change_password": false
  }
}
```

### 2. POST `/api/auth/logout`

API 登出端点

**查询参数：**
- `username`: 用户名

**响应：**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### 3. POST `/api/auth/refresh/{username}`

手动刷新指定用户的 Token

**路径参数：**
- `username`: 用户名

**响应：**
```json
{
  "success": true,
  "message": "Token refreshed successfully"
}
```

## 架构设计

### 单例模式

使用 `@lru_cache()` 装饰器实现 `AuthService` 单例模式：

```python
@lru_cache()
def get_auth_service() -> AuthService:
    """获取认证服务单例实例"""
    return AuthService()
```

所有模块通过 `get_auth_service()` 获取同一个 `AuthService` 实例，确保：
- Token 存储在同一个内存空间
- 后台刷新任务和认证服务共享 Token

### Token 存储

`TokenStore` 类提供简单的内存存储：

```python
class TokenStore:
    def save_token(username, access_token, refresh_token)
    def get_token(username) -> dict | None
    def remove_token(username)
    def get_all_tokens() -> dict
```

存储格式：
```python
{
    "username": {
        "access_token": "...",
        "refresh_token": "...",
        "updated_at": datetime(...)
    }
}
```

### 后台任务

后台 Token 刷新任务在应用启动时创建：

```python
async def token_refresh_task(auth_service: AuthService):
    """定期刷新 OAuth2 Token 的后台任务"""
    while True:
        await asyncio.sleep(settings.oauth2_token_refresh_interval)
        if settings.oauth2_enabled:
            auth_service.refresh_all_tokens()
```

应用关闭时会优雅地取消该任务。

## 切换认证模式

### 使用 OAuth2 认证

在 `.env` 文件中设置：
```bash
OAUTH2_ENABLED=True
```

### 使用本地认证

在 `.env` 文件中设置：
```bash
OAUTH2_ENABLED=False
```

本地认证将使用 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 进行验证。

## 安全建议

1. **生产环境配置**
   - 使用 HTTPS 协议访问 OAuth2 服务器
   - 定期更换 `SECRET_KEY`
   - 限制 CORS 允许的域名

2. **Token 安全**
   - Token 仅存储在服务器内存中，不会发送到客户端
   - 定期刷新 Token 减少泄露风险
   - 用户登出时立即清除 Token

3. **权限控制**
   - 仅允许 `is_superuser=true` 的用户登录
   - 在关键操作前验证用户权限

## 故障处理

### OAuth2 服务不可用

- 系统会返回 503 Service Unavailable
- 可临时切换到本地认证模式

### Token 刷新失败

- 自动清除失败用户的 Token
- 用户需重新登录获取新 Token

### 日志监控

系统会记录以下关键事件：
- 用户登录/登出
- Token 刷新成功/失败
- OAuth2 服务连接错误

查看日志：
```bash
# 查看应用日志
./run.sh dev
```

## 测试示例

### 使用 curl 测试登录

```bash
# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123"
  }'

# 刷新 Token
curl -X POST http://localhost:8000/api/auth/refresh/admin

# 登出
curl -X POST http://localhost:8000/api/auth/logout?username=admin
```

## 参考文档

- OAuth2 认证服务 API: http://core.seadee.com.cn:8099/docs
- OAuth2 RFC 6749: https://tools.ietf.org/html/rfc6749
