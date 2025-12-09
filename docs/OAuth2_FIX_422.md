# OAuth2 认证请求格式修复

## 问题描述

在使用 OAuth2 外部认证时，登录请求返回 422 错误：

```
OAuth2 authentication failed for admin: 422
{"detail":[
  {"type":"missing","loc":["body","username"],"msg":"Field required",...},
  {"type":"missing","loc":["body","password"],"msg":"Field required",...}
]}
```

## 根本原因

OAuth2 标准（RFC 6749）规定，密码模式的 Token 请求应该使用 **`application/x-www-form-urlencoded`** 格式，而不是 JSON 格式。

我们原先的实现错误地使用了：
```python
# ❌ 错误：使用 JSON 格式
response = requests.post(token_url, json=token_request.model_dump(), timeout=10)
```

## 解决方案

修改为使用表单数据格式：
```python
# ✅ 正确：使用 form-urlencoded 格式
token_data = {
    "username": username,
    "password": password,
    "grant_type": "password"
}
response = requests.post(token_url, data=token_data, timeout=10)
```

## 修复的文件

### 1. [app/services/auth_service.py](../app/services/auth_service.py)

#### 登录请求（第 99-115 行）
```python
def _authenticate_oauth2(self, username: str, password: str) -> tuple[str, UserInfo]:
    """OAuth2 认证"""
    try:
        token_url = f"{settings.oauth2_server_url}{settings.oauth2_token_endpoint}"

        # OAuth2 标准使用 form-urlencoded 格式
        token_data = {
            "username": username,
            "password": password,
            "grant_type": "password"
        }

        response = requests.post(token_url, data=token_data, timeout=10)  # ✅ 使用 data
```

#### Token 刷新请求（第 205-218 行）
```python
def refresh_token(self, username: str) -> bool:
    try:
        refresh_url = f"{settings.oauth2_server_url}{settings.oauth2_refresh_endpoint}"

        # OAuth2 标准使用 form-urlencoded 格式
        refresh_data = {
            "refresh_token": token_data["refresh_token"]
        }

        response = requests.post(refresh_url, data=refresh_data, timeout=10)  # ✅ 使用 data
```

### 2. [test_oauth2.py](../test_oauth2.py)

#### 登录测试（第 51 行）
```python
response = requests.post(token_url, data=login_data, timeout=10)  # ✅ 使用 data
```

#### 刷新测试（第 91 行）
```python
response = requests.post(refresh_url, data=refresh_data, timeout=10)  # ✅ 使用 data
```

### 3. [docs/OAuth2_Authentication.md](../docs/OAuth2_Authentication.md)

更新了文档说明，明确指出使用 `application/x-www-form-urlencoded` 格式：

```bash
# 登录请求示例
curl -X POST http://core.seadee.com.cn:8099/auth/token \
  -d "username=admin" \
  -d "password=Admin123" \
  -d "grant_type=password"

# 刷新请求示例
curl -X POST http://core.seadee.com.cn:8099/auth/refresh \
  -d "refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 验证修复

### 1. 运行测试脚本
```bash
python test_oauth2.py
```

预期输出：
```
✅ 登录成功!
   Access Token (前50字符): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Refresh Token (前50字符): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

✅ 成功获取用户信息:
   用户名: admin
   是否超级用户: True

✅ Token 刷新成功!
```

### 2. 启动应用并测试登录
```bash
./run.sh dev
```

访问 http://localhost:8000/login 并使用超级用户凭证登录。

## OAuth2 标准说明

根据 [RFC 6749 Section 4.3.2](https://tools.ietf.org/html/rfc6749#section-4.3.2)，Resource Owner Password Credentials Grant（密码模式）的 Token 请求必须使用 `application/x-www-form-urlencoded` 格式：

> The client makes a request to the token endpoint by adding the
> following parameters using the "application/x-www-form-urlencoded"
> format...

### 正确的请求格式

**Content-Type:** `application/x-www-form-urlencoded`

**请求体：**
```
grant_type=password&username=admin&password=Admin123
```

### Python requests 库用法

- ✅ **使用 `data` 参数** → 自动设置 `Content-Type: application/x-www-form-urlencoded`
  ```python
  requests.post(url, data={"key": "value"})
  ```

- ❌ **使用 `json` 参数** → 设置 `Content-Type: application/json`
  ```python
  requests.post(url, json={"key": "value"})  # 不适用于 OAuth2 Token 请求
  ```

## 影响范围

此修复影响以下功能：
- ✅ 用户登录
- ✅ Token 自动刷新
- ✅ 手动 Token 刷新 API

## 兼容性

- ✅ 符合 OAuth2 RFC 6749 标准
- ✅ 兼容标准 OAuth2 服务器
- ✅ 不影响本地认证模式

## 总结

这是一个标准合规性修复，确保我们的 OAuth2 客户端实现符合 RFC 6749 规范，使用正确的请求格式与认证服务器通信。

---

**修复日期:** 2025-12-09
**状态:** ✅ 已完成并验证
