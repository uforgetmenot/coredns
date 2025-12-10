# 上级 DNS 配置功能 - 文件修改清单

## 新增文件

### 后端文件
1. **app/schemas/settings.py**
   - 定义上级 DNS 配置的 Pydantic 模型
   - 包含数据验证逻辑

2. **app/services/settings_service.py**
   - 系统设置服务类
   - 处理上级 DNS 的 CRUD 操作

3. **app/api/settings.py**
   - 上级 DNS 配置的 REST API 端点
   - GET /api/settings/upstream-dns
   - PUT /api/settings/upstream-dns

### 测试文件
4. **tests/test_settings.py**
   - 设置服务的单元测试
   - 5 个测试用例，全部通过

5. **tests/test_corefile_upstream_dns.py**
   - Corefile 生成集成测试
   - 3 个测试用例，全部通过

### 文档文件
6. **docs/upstream-dns-feature.md**
   - 详细的功能文档
   - 包含使用方法和 API 文档

7. **docs/upstream-dns-quickstart.md**
   - 快速开始指南
   - 常用 DNS 服务器参考

8. **IMPLEMENTATION_SUMMARY.md**
   - 实现总结文档
   - 完整的功能清单

9. **CHANGES.md** (本文件)
   - 修改清单

## 修改文件

### 后端文件
1. **app/main.py**
   - 第 19 行: 添加导入 `from app.api import settings as settings_api`
   - 第 106 行: 注册设置 API 路由 `application.include_router(settings_api.router)`

2. **app/templates/Corefile.j2**
   - 第 19 行: 更新 forward 指令支持动态 DNS
   - 原: `forward . 223.5.5.5 223.6.6.6`
   - 新: `forward . {{ primary_dns }}{% if secondary_dns %} {{ secondary_dns }}{% endif %}`

3. **app/services/corefile_service.py**
   - 第 52-62 行: 在 `generate_corefile` 方法中添加获取上级 DNS 配置的逻辑
   - 从 SettingsService 读取 DNS 配置
   - 将配置传递给模板渲染

### 前端文件
4. **app/templates/dashboard.html**
   - 第 52-91 行: 添加"上级 DNS 配置"卡片
   - 包含两个输入框（主 DNS 和备用 DNS）
   - 添加保存按钮

5. **app/static/js/dashboard.js**
   - 第 10 行: 添加表单事件监听器
   - 第 17 行: 在数据加载中添加 `loadUpstreamDNS()`
   - 第 97-128 行: 添加两个新函数
     - `loadUpstreamDNS()`: 加载当前配置
     - `handleUpstreamDNSSubmit()`: 处理表单提交

## 配置影响

### 数据库
- 使用现有的 `system_settings` 表
- 新增两条配置记录：
  - `upstream_primary_dns`
  - `upstream_secondary_dns`

### API 端点
- 新增 2 个 REST API 端点
- 使用 `/api/settings` 前缀

### 环境变量
- 无需新增环境变量
- 使用数据库存储配置

## 依赖关系

### Python 包
- 无需新增依赖
- 使用现有的：
  - FastAPI
  - SQLModel
  - Pydantic
  - Jinja2

### 前端
- 无需新增依赖
- 使用现有的 JavaScript

## 测试覆盖

### 单元测试
- 设置服务: 5 个测试
- Corefile 生成: 3 个测试
- 模型测试: 保持现有测试通过

### 总计
- 新增: 8 个测试
- 通过率: 100%

## 兼容性

### 向后兼容
- ✅ 不影响现有功能
- ✅ 未配置时使用默认值
- ✅ 现有 Corefile 生成逻辑保持兼容

### 数据库迁移
- ✅ 无需迁移
- ✅ 使用现有表结构
- ✅ 自动创建配置记录

## 部署清单

### 代码部署
1. 拉取最新代码
2. 重启应用服务

### 数据库
- 无需手动迁移
- 首次使用会自动初始化默认配置

### 验证步骤
1. 访问 Dashboard 页面
2. 检查"上级 DNS 配置"卡片是否显示
3. 测试保存配置功能
4. 生成 Corefile 并检查 forward 指令
5. 运行测试: `pytest tests/test_settings.py tests/test_corefile_upstream_dns.py -v`

## 回滚方案

如需回滚，只需还原以下文件：
1. app/main.py
2. app/templates/Corefile.j2
3. app/services/corefile_service.py
4. app/templates/dashboard.html
5. app/static/js/dashboard.js

删除新增文件即可完成回滚。

## 联系方式

如有问题，请参考：
- 功能文档: `docs/upstream-dns-feature.md`
- 快速开始: `docs/upstream-dns-quickstart.md`
- 实现总结: `IMPLEMENTATION_SUMMARY.md`
