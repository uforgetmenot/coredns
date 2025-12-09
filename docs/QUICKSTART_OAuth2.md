# OAuth2 认证快速开始指南

## 快速配置

### 1. 更新环境配置

编辑 `.env` 文件，添加 OAuth2 配置：

```bash
# OAuth2 外部认证配置
OAUTH2_ENABLED=True
OAUTH2_SERVER_URL=http://core.seadee.com.cn:8099
OAUTH2_TOKEN_ENDPOINT=/auth/token
OAUTH2_USERINFO_ENDPOINT=/auth/me
OAUTH2_REFRESH_ENDPOINT=/auth/refresh
OAUTH2_TOKEN_REFRESH_INTERVAL=3600
```

### 2. 测试 OAuth2 服务器连接

运行测试脚本验证配置：

```bash
python test_oauth2.py
```

### 3. 启动应用

```bash
./run.sh dev
```

### 4. 访问登录页面

打开浏览器访问：http://localhost:8000/login

使用 OAuth2 服务器的超级用户凭证登录（例如 `admin` / `Admin123`）

## 关键特性

✅ **仅超级用户可登录**
系统会验证用户的 `is_superuser` 标志，非超级用户将被拒绝登录

✅ **自动刷新 Token**
后台任务每小时（可配置）自动刷新所有在线用户的 Access Token

✅ **双模式支持**
可在 OAuth2 认证和本地认证之间切换（通过 `OAUTH2_ENABLED` 配置）

## 切换到本地认证

如果 OAuth2 服务不可用，可临时切换到本地认证：

1. 编辑 `.env` 文件：
   ```bash
   OAUTH2_ENABLED=False
   ```

2. 重启应用

3. 使用本地凭证登录：
   - 用户名：`ADMIN_USERNAME` 的值（默认 `admin`）
   - 密码：`ADMIN_PASSWORD` 的值（默认 `admin123`）

## API 端点

### 登录
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "Admin123"
}
```

### 登出
```bash
POST /api/auth/logout?username=admin
```

### 手动刷新 Token
```bash
POST /api/auth/refresh/admin
```

## 故障排查

### 无法连接到 OAuth2 服务器

**错误信息：** "Authentication service unavailable"

**解决方案：**
1. 检查网络连接
2. 验证 `OAUTH2_SERVER_URL` 配置是否正确
3. 临时切换到本地认证模式

### 登录失败：Only superusers are allowed

**错误信息：** "Only superusers are allowed to login"

**解决方案：**
1. 确保使用的账户在 OAuth2 服务器上是超级用户
2. 联系系统管理员提升账户权限

### Token 刷新失败

**表现：** 用户需要频繁重新登录

**解决方案：**
1. 检查应用日志中的刷新错误信息
2. 验证 `OAUTH2_REFRESH_ENDPOINT` 配置
3. 确保 Refresh Token 未过期

## 查看日志

应用启动时会显示 OAuth2 状态：

```
🚀 CoreDNS Manager starting...
📊 Debug mode: False
📁 Database: sqlite:///./data/db/coredns.db
📄 Corefile: ./data/Corefile
🔐 OAuth2 enabled: True
⏱️  Starting token refresh task (interval: 3600s)
```

查看实时日志：
```bash
./run.sh dev
```

## 详细文档

完整文档请参考：[docs/OAuth2_Authentication.md](OAuth2_Authentication.md)

## 技术支持

如有问题，请查看：
- API 文档：http://localhost:8000/docs
- OAuth2 服务文档：http://core.seadee.com.cn:8099/docs
