# 上级 DNS 配置功能

## 功能概述

此功能允许通过 Web 界面配置 CoreDNS 的上级 DNS 服务器（最多支持两个）。配置会自动应用到生成的 Corefile 中的 `forward` 指令。

## 功能特性

- ✅ 支持配置主 DNS 服务器（必填）
- ✅ 支持配置备用 DNS 服务器（可选）
- ✅ 配置实时保存到数据库
- ✅ 自动应用到 Corefile 生成
- ✅ Web 界面可视化配置
- ✅ API 端点支持

## 使用方法

### 通过 Web 界面配置

1. 访问 Dashboard 页面（`/dashboard`）
2. 找到"上级 DNS 配置"卡片
3. 填写主 DNS 服务器地址（必填）
4. 填写备用 DNS 服务器地址（可选）
5. 点击"保存配置"按钮

### 通过 API 配置

#### 获取当前配置

```bash
GET /api/settings/upstream-dns
```

响应示例：
```json
{
  "success": true,
  "data": {
    "primary_dns": "223.5.5.5",
    "secondary_dns": "223.6.6.6"
  },
  "message": "Upstream DNS settings retrieved successfully"
}
```

#### 更新配置

```bash
PUT /api/settings/upstream-dns
Content-Type: application/json

{
  "primary_dns": "1.1.1.1",
  "secondary_dns": "1.0.0.1"
}
```

响应示例：
```json
{
  "success": true,
  "data": {
    "primary_dns": "1.1.1.1",
    "secondary_dns": "1.0.0.1"
  },
  "message": "Upstream DNS settings updated successfully"
}
```

#### 只配置主 DNS

```bash
PUT /api/settings/upstream-dns
Content-Type: application/json

{
  "primary_dns": "1.1.1.1",
  "secondary_dns": null
}
```

## Corefile 生成示例

### 配置了两个 DNS 服务器

```
. {
    forward . 223.5.5.5 223.6.6.6
    log
    errors
    cache 30
}
```

### 只配置了主 DNS 服务器

```
. {
    forward . 1.1.1.1
    log
    errors
    cache 30
}
```

## 技术实现

### 数据库模型

使用 `SystemSetting` 模型存储配置：
- `upstream_primary_dns`: 主 DNS 服务器地址
- `upstream_secondary_dns`: 备用 DNS 服务器地址（可选）

### 服务层

- `SettingsService`: 管理系统设置的服务类
  - `get_upstream_dns()`: 获取上级 DNS 配置
  - `set_upstream_dns()`: 设置上级 DNS 配置
  - `initialize_default_settings()`: 初始化默认设置

### API 层

- `GET /api/settings/upstream-dns`: 获取上级 DNS 配置
- `PUT /api/settings/upstream-dns`: 更新上级 DNS 配置

### 前端

- Dashboard 页面新增"上级 DNS 配置"卡片
- JavaScript 自动加载和保存配置
- 实时反馈操作结果

## 默认配置

如果未配置上级 DNS，系统将使用以下默认值：
- 主 DNS: `223.5.5.5` (Google DNS)
- 备用 DNS: `223.6.6.6` (Google DNS)

## 测试

运行测试：
```bash
# 测试设置服务
python3 -m pytest tests/test_settings.py -v

# 测试 Corefile 生成
python3 -m pytest tests/test_corefile_upstream_dns.py -v
```

## 相关文件

### 后端
- [app/schemas/settings.py](app/schemas/settings.py) - 设置相关的 Pydantic 模型
- [app/services/settings_service.py](app/services/settings_service.py) - 设置服务类
- [app/api/settings.py](app/api/settings.py) - 设置 API 路由
- [app/services/corefile_service.py](app/services/corefile_service.py) - Corefile 生成服务（已更新）
- [app/templates/Corefile.j2](app/templates/Corefile.j2) - Corefile 模板（已更新）

### 前端
- [app/templates/dashboard.html](app/templates/dashboard.html) - Dashboard 页面（已更新）
- [app/static/js/dashboard.js](app/static/js/dashboard.js) - Dashboard JavaScript（已更新）

### 测试
- [tests/test_settings.py](tests/test_settings.py) - 设置服务测试
- [tests/test_corefile_upstream_dns.py](tests/test_corefile_upstream_dns.py) - Corefile 生成测试

## 注意事项

1. 主 DNS 服务器地址是必填项
2. 备用 DNS 服务器地址是可选项，可以设置为 `null` 或留空
3. DNS 地址支持 IPv4 和 IPv6 格式
4. 更新配置后需要重新生成 Corefile 才能生效
5. 可以在 Dashboard 页面一键重载 CoreDNS 使配置生效
