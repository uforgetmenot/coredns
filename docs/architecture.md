# 上级 DNS 配置功能架构

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户界面层                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Dashboard (dashboard.html)                                  │
│  ┌───────────────────────────────────────┐                  │
│  │  上级 DNS 配置卡片                     │                  │
│  │  ┌─────────────────────────────────┐  │                  │
│  │  │ 主 DNS: [1.1.1.1        ]      │  │                  │
│  │  │ 备 DNS: [1.0.0.1        ]      │  │                  │
│  │  │         [保存配置]              │  │                  │
│  │  └─────────────────────────────────┘  │                  │
│  └───────────────────────────────────────┘                  │
│                                                               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Request/Response
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                         API 层                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  settings.py (API Router)                                    │
│  ┌──────────────────────────────────────────────────┐       │
│  │ GET  /api/settings/upstream-dns                  │       │
│  │      → get_upstream_dns()                        │       │
│  │                                                   │       │
│  │ PUT  /api/settings/upstream-dns                  │       │
│  │      → update_upstream_dns()                     │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└────────────────────┬────────────────────────────────────────┘
                     │ Function Calls
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                        服务层                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SettingsService                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │ • get_upstream_dns()                             │       │
│  │   → 从数据库读取 DNS 配置                         │       │
│  │                                                   │       │
│  │ • set_upstream_dns(primary, secondary)           │       │
│  │   → 保存 DNS 配置到数据库                         │       │
│  │                                                   │       │
│  │ • initialize_default_settings()                  │       │
│  │   → 初始化默认 DNS 配置                          │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
│  CorefileService                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │ • generate_corefile()                            │       │
│  │   → 读取 DNS 配置                                │       │
│  │   → 渲染 Jinja2 模板                             │       │
│  │   → 生成 Corefile 内容                           │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└────────────────────┬────────────────────────────────────────┘
                     │ Database Queries
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SystemSetting Model                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Table: system_settings                           │       │
│  │ ┌────────────────────────────────────────────┐   │       │
│  │ │ id  │ key                  │ value          │   │       │
│  │ ├─────┼──────────────────────┼────────────────┤   │       │
│  │ │ 1   │ upstream_primary_dns │ 1.1.1.1        │   │       │
│  │ │ 2   │ upstream_secondary_dns│ 1.0.0.1       │   │       │
│  │ └────────────────────────────────────────────┘   │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└────────────────────┬────────────────────────────────────────┘
                     │ Template Rendering
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      Corefile 生成                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Corefile.j2 (Jinja2 Template)                              │
│  ┌──────────────────────────────────────────────────┐       │
│  │ . {                                              │       │
│  │     forward . {{ primary_dns }}                  │       │
│  │              {% if secondary_dns %}              │       │
│  │              {{ secondary_dns }}                 │       │
│  │              {% endif %}                         │       │
│  │     log                                          │       │
│  │     errors                                       │       │
│  │     cache 30                                     │       │
│  │ }                                                │       │
│  └──────────────────────────────────────────────────┘       │
│                              ↓                                │
│  生成的 Corefile                                             │
│  ┌──────────────────────────────────────────────────┐       │
│  │ . {                                              │       │
│  │     forward . 1.1.1.1 1.0.0.1                   │       │
│  │     log                                          │       │
│  │     errors                                       │       │
│  │     cache 30                                     │       │
│  │ }                                                │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 数据流向

### 1. 获取配置流程
```
用户访问 Dashboard
    ↓
dashboard.js 调用 loadUpstreamDNS()
    ↓
GET /api/settings/upstream-dns
    ↓
SettingsService.get_upstream_dns()
    ↓
查询 system_settings 表
    ↓
返回 JSON 响应
    ↓
填充表单字段
```

### 2. 保存配置流程
```
用户填写表单 → 点击"保存配置"
    ↓
dashboard.js 调用 handleUpstreamDNSSubmit()
    ↓
PUT /api/settings/upstream-dns
    ↓
验证请求数据 (schemas/settings.py)
    ↓
SettingsService.set_upstream_dns()
    ↓
更新/插入 system_settings 表
    ↓
返回成功响应
    ↓
显示成功提示
```

### 3. Corefile 生成流程
```
用户点击"生成 Corefile"
    ↓
POST /api/corefile/generate
    ↓
CorefileService.generate_corefile()
    ↓
SettingsService.get_upstream_dns()
    ↓
读取 DNS 记录和 DNS 配置
    ↓
Jinja2 渲染模板 (Corefile.j2)
    ↓
写入 Corefile 文件
    ↓
可选：重载 CoreDNS
```

## 技术栈

### 前端
- HTML5
- JavaScript (ES6+)
- TailwindCSS + DaisyUI

### 后端
- Python 3.11+
- FastAPI
- SQLModel (SQLAlchemy + Pydantic)
- Jinja2

### 数据库
- SQLite3

## 关键组件

### 1. Schema 验证
```python
class UpdateUpstreamDNSRequest(BaseModel):
    primary_dns: str  # 必填
    secondary_dns: Optional[str]  # 可选

    @validator("primary_dns", "secondary_dns")
    def validate_dns_address(cls, v):
        # DNS 地址格式验证
```

### 2. 数据持久化
```python
class SettingsService:
    def set_upstream_dns(self, primary, secondary):
        # 保存到 system_settings 表
        # 键: upstream_primary_dns, upstream_secondary_dns
```

### 3. 模板渲染
```jinja2
forward . {{ primary_dns }}
{% if secondary_dns %} {{ secondary_dns }}{% endif %}
```

## 设计原则

1. **单一职责**: 每个组件只负责一个功能
2. **松耦合**: 层与层之间通过接口通信
3. **可测试性**: 每个层都有对应的测试
4. **向后兼容**: 不影响现有功能
5. **用户友好**: 提供清晰的 UI 和 API

## 扩展性

### 支持更多 DNS 服务器
在 `SettingsService` 中添加更多 DNS 配置项：
```python
KEY_TERTIARY_DNS = "upstream_tertiary_dns"
```

### 支持 DNS 协议选择
添加协议类型配置：
```python
KEY_DNS_PROTOCOL = "upstream_dns_protocol"  # udp, tcp, https, tls
```

### 支持 DNS 端口配置
添加端口配置：
```python
KEY_DNS_PORT = "upstream_dns_port"  # 默认 53
```
