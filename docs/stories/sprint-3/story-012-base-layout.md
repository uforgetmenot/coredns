# Story-012: 基础布局和导航

## 基本信息
- **故事ID**: Story-012
- **所属Sprint**: Sprint 3
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 一个清晰的 Web 界面布局和导航系统
**So that** 我可以方便地访问各个功能模块

## 背景描述
Web 界面是用户与系统交互的主要方式，需要提供响应式布局、清晰的导航结构和统一的 UI 组件。使用现代前端框架构建单页应用（SPA）。

## 验收标准

- [ ] AC1: 基础 HTML 模板已创建
  - 使用 Jinja2 模板引擎
  - 包含 HTML5 基础结构
  - 引入 CSS 和 JavaScript 资源

- [ ] AC2: 响应式布局已实现
  - 顶部导航栏（Header）
  - 侧边菜单栏（Sidebar）
  - 主内容区域（Main Content）
  - 底部信息栏（Footer）
  - 支持移动端和桌面端

- [ ] AC3: 导航菜单已实现
  - DNS 记录管理
  - Zone 管理
  - Corefile 管理
  - 系统监控
  - 系统设置
  - 高亮当前活动页面

- [ ] AC4: UI 框架已集成
  - 使用 Bootstrap 5 或 Tailwind CSS
  - 或使用 Vue.js/React 组件库
  - 统一的颜色主题和样式

- [ ] AC5: 基础组件已实现
  - 按钮组件（主要、次要、危险）
  - 表单组件（输入框、选择框、复选框）
  - 提示消息组件（成功、错误、警告）
  - 加载状态组件
  - 分页组件

- [ ] AC6: 静态资源服务
  - FastAPI 静态文件服务配置
  - CSS 文件组织
  - JavaScript 文件组织
  - 图标和图片资源

- [ ] AC7: 首页已实现
  - 显示系统概览
  - 快速统计信息（记录总数、Zone 数量等）
  - 快速操作入口

## 技术实现要点

### 1. 基础 HTML 模板（app/templates/base.html）
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CoreDNS Manager{% endblock %}</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{{ url_for('static', path='/css/style.css') }}">

    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Top Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">
                <i class="fas fa-network-wired"></i> CoreDNS Manager
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/docs" target="_blank">
                            <i class="fas fa-book"></i> API 文档
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <nav class="col-md-2 d-md-block bg-light sidebar">
                <div class="position-sticky pt-3">
                    <ul class="nav flex-column">
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'dashboard' %}active{% endif %}" href="/">
                                <i class="fas fa-tachometer-alt"></i> 控制台
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'records' %}active{% endif %}" href="/records">
                                <i class="fas fa-list"></i> DNS 记录
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'zones' %}active{% endif %}" href="/zones">
                                <i class="fas fa-globe"></i> Zone 管理
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'corefile' %}active{% endif %}" href="/corefile">
                                <i class="fas fa-file-code"></i> Corefile
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'monitoring' %}active{% endif %}" href="/monitoring">
                                <i class="fas fa-chart-line"></i> 系统监控
                            </a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link {% if active_page == 'settings' %}active{% endif %}" href="/settings">
                                <i class="fas fa-cog"></i> 系统设置
                            </a>
                        </li>
                    </ul>
                </div>
            </nav>

            <!-- Main Content -->
            <main class="col-md-10 ms-sm-auto px-md-4">
                <!-- Alert Messages -->
                <div id="alert-container" class="mt-3"></div>

                <!-- Page Content -->
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <!-- Footer -->
    <footer class="footer mt-auto py-3 bg-light">
        <div class="container text-center">
            <span class="text-muted">CoreDNS Manager © 2025</span>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Axios for API calls -->
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <!-- Custom JS -->
    <script src="{{ url_for('static', path='/js/main.js') }}"></script>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 2. 首页模板（app/templates/index.html）
```html
{% extends "base.html" %}

{% block title %}控制台 - CoreDNS Manager{% endblock %}

{% block content %}
<div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
    <h1 class="h2">控制台</h1>
</div>

<!-- Statistics Cards -->
<div class="row mb-4">
    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-primary shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                            DNS 记录总数
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="total-records">-</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-list fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-success shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                            活跃记录
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="active-records">-</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-check-circle fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-info shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                            Zone 数量
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="total-zones">-</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-globe fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="col-xl-3 col-md-6 mb-4">
        <div class="card border-left-warning shadow h-100 py-2">
            <div class="card-body">
                <div class="row no-gutters align-items-center">
                    <div class="col mr-2">
                        <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                            CoreDNS 状态
                        </div>
                        <div class="h5 mb-0 font-weight-bold text-gray-800" id="coredns-status">-</div>
                    </div>
                    <div class="col-auto">
                        <i class="fas fa-server fa-2x text-gray-300"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Quick Actions -->
<div class="row">
    <div class="col-12">
        <h4>快速操作</h4>
        <div class="list-group">
            <a href="/records/new" class="list-group-item list-group-item-action">
                <i class="fas fa-plus-circle text-primary"></i> 添加 DNS 记录
            </a>
            <a href="/corefile" class="list-group-item list-group-item-action">
                <i class="fas fa-sync text-success"></i> 生成 Corefile
            </a>
            <a href="/monitoring" class="list-group-item list-group-item-action">
                <i class="fas fa-chart-line text-info"></i> 查看系统监控
            </a>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Load dashboard statistics
    async function loadDashboardStats() {
        try {
            // Load DNS records stats
            const recordsRes = await axios.get('/api/records?page_size=1');
            document.getElementById('total-records').textContent = recordsRes.data.pagination.total;

            const activeRes = await axios.get('/api/records?status=active&page_size=1');
            document.getElementById('active-records').textContent = activeRes.data.pagination.total;

            // Load CoreDNS status
            const statusRes = await axios.get('/api/coredns/status');
            const status = statusRes.data.data.running ? '运行中' : '已停止';
            document.getElementById('coredns-status').textContent = status;

            // TODO: Load zones count when Zone API is implemented
            document.getElementById('total-zones').textContent = '-';

        } catch (error) {
            console.error('Failed to load dashboard stats:', error);
        }
    }

    // Load stats on page load
    document.addEventListener('DOMContentLoaded', loadDashboardStats);
</script>
{% endblock %}
```

### 3. 自定义 CSS（app/static/css/style.css）
```css
/* Custom styles for CoreDNS Manager */

body {
    font-size: 0.875rem;
}

.sidebar {
    position: fixed;
    top: 56px;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, .1);
}

.sidebar .nav-link {
    font-weight: 500;
    color: #333;
    padding: 0.75rem 1rem;
}

.sidebar .nav-link.active {
    color: #007bff;
    background-color: #e9ecef;
}

.sidebar .nav-link:hover {
    color: #007bff;
}

main {
    padding-top: 56px;
    min-height: calc(100vh - 56px);
}

.border-left-primary {
    border-left: 0.25rem solid #4e73df !important;
}

.border-left-success {
    border-left: 0.25rem solid #1cc88a !important;
}

.border-left-info {
    border-left: 0.25rem solid #36b9cc !important;
}

.border-left-warning {
    border-left: 0.25rem solid #f6c23e !important;
}

.footer {
    margin-top: 2rem;
}
```

### 4. 通用 JavaScript（app/static/js/main.js）
```javascript
// Common utilities for CoreDNS Manager

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    alertContainer.innerHTML = alertHtml;

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertContainer.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }
    }, 5000);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// Handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    let message = '操作失败';

    if (error.response) {
        message = error.response.data.detail || message;
    } else if (error.request) {
        message = '网络错误，请检查连接';
    }

    showAlert(message, 'danger');
}
```

### 5. 页面路由（app/api/pages.py）
```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 控制台"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "active_page": "dashboard"
    })
```

### 6. 静态文件配置（app/main.py）
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="CoreDNS Manager")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include page router
from app.api import pages
app.include_router(pages.router)
```

## 依赖关系
- **前置依赖**:
  - Story-001 (需要基础项目结构)
- **后置依赖**:
  - Story-013 (DNS 记录列表页面)
  - Story-014 (DNS 记录表单)
  - Story-015 (搜索界面)
  - Story-017 (Zone 管理界面)

## 测试用例

### 测试场景 1: 首页可访问
```python
def test_index_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "CoreDNS Manager" in response.text
```

### 测试场景 2: 静态资源可访问
```python
def test_static_files():
    response = client.get("/static/css/style.css")
    assert response.status_code == 200

    response = client.get("/static/js/main.js")
    assert response.status_code == 200
```

### 测试场景 3: 导航菜单渲染
```python
def test_navigation_menu():
    response = client.get("/")
    assert "DNS 记录" in response.text
    assert "Zone 管理" in response.text
    assert "Corefile" in response.text
```

### 测试场景 4: 响应式布局
```python
def test_responsive_layout():
    response = client.get("/")
    # 检查 Bootstrap 类
    assert "navbar" in response.text
    assert "sidebar" in response.text
    assert "container-fluid" in response.text
```

## 完成定义 (Definition of Done)
- [ ] 基础 HTML 模板已创建
- [ ] 所有验收标准已满足
- [ ] 响应式布局已实现
- [ ] 导航菜单已实现
- [ ] 静态资源服务已配置
- [ ] 首页已实现
- [ ] CSS 和 JavaScript 文件已创建
- [ ] 页面路由已实现
- [ ] 单元测试通过
- [ ] 代码已合并到 `develop` 分支

## 参考资料
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Font Awesome Icons](https://fontawesome.com/)

## 备注
- 可以考虑使用前端框架（Vue.js, React）构建更复杂的交互
- 可以添加暗黑模式支持
- 可以添加多语言支持
- 考虑添加用户认证和权限管理（后续版本）

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
