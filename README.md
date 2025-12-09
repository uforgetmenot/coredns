# CoreDNS Manager

CoreDNS 管理工具 - 提供可视化的 Web 界面管理 CoreDNS 的 DNS 记录。

## 功能特性

- ✅ DNS 记录的增删改查
- ✅ 按 Zone 分组管理
- ✅ 搜索和过滤功能
- ✅ 自动生成 Corefile 配置
- ✅ CoreDNS 无缝重载
- ✅ 操作日志记录
- ✅ 系统监控和状态展示

## 技术栈

- **后端**: FastAPI + Python 3.11+
- **ORM**: SQLModel
- **数据库**: SQLite3
- **模板引擎**: Jinja2
- **前端**: TailwindCSS + DaisyUI
- **容器化**: Docker + Docker Compose
- **依赖管理**: Poetry

## 快速开始

### 前置要求

- Python 3.11+
- Poetry 1.7+
- Docker (可选，用于容器化部署)

### 开发环境安装

1. 克隆项目
\`\`\`bash
git clone <repository-url>
cd coredns
\`\`\`

2. 安装依赖
\`\`\`bash
# 使用 Poetry 安装依赖
poetry install

# 或者激活虚拟环境
poetry shell
\`\`\`

3. 配置环境变量
\`\`\`bash
# 复制环境变量示例文件
cp .env.example .env

# 根据需要修改 .env 文件
\`\`\`

4. 启动开发服务器
\`\`\`bash
# 使用 Poetry 运行
poetry run uvicorn app.main:app --reload

# 或在 Poetry shell 中运行
uvicorn app.main:app --reload
\`\`\`

5. 访问应用
- 管理界面: http://localhost:8000/login （默认账号：admin/admin123）
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### Web 管理界面

启动服务后访问 `/login`，使用 `.env` 中配置的 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 登录。

- Dashboard 卡片实时展示 CoreDNS 状态、记录数、Zone 数等指标
- 内置 DNS 记录管理：新增/编辑/删除、筛选与搜索
- Corefile 预览与一键生成、可直接触发 CoreDNS 重载
- Corefile 备份列表支持恢复与删除

## Docker 部署

### 快速启动

\`\`\`bash
# 准备 Corefile
cp docker/Corefile data/Corefile

# 启动服务
docker-compose up -d
\`\`\`

### 常用命令

\`\`\`bash
# 查看日志
docker-compose logs -f coredns-manager

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重建镜像
docker-compose build --no-cache
\`\`\`

## 开发指南

### 项目结构

\`\`\`
coredns/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic 模型
│   ├── api/               # API 路由
│   ├── services/          # 业务逻辑层
│   ├── utils/             # 工具函数
│   ├── templates/         # Jinja2 模板
│   └── static/            # 静态文件
├── tests/                 # 测试文件
├── data/                  # 数据目录
│   ├── Corefile          # CoreDNS 配置文件
│   └── db/               # SQLite 数据库
├── docs/                  # 文档
│   ├── prd.md            # 产品需求文档
│   └── stories/          # 开发故事
├── pyproject.toml         # Poetry 配置
├── docker-compose.yml     # Docker Compose 配置
├── Dockerfile             # Docker 镜像配置
└── README.md              # 项目说明
\`\`\`

### 运行测试

\`\`\`bash
# 运行所有测试
poetry run pytest

# 运行测试并查看覆盖率
poetry run pytest --cov=app tests/

# 运行特定测试文件
poetry run pytest tests/test_health.py
\`\`\`

### 代码格式化

\`\`\`bash
# 使用 Black 格式化代码
poetry run black app/ tests/

# 使用 Flake8 检查代码
poetry run flake8 app/ tests/

# 使用 MyPy 类型检查
poetry run mypy app/
\`\`\`

## API 文档

启动服务后，访问以下 URL 查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 URL | sqlite:///./data/db/coredns.db |
| COREFILE_PATH | Corefile 路径 | ./data/Corefile |
| COREDNS_CONTAINER_NAME | CoreDNS 容器名称 | coredns |
| LOG_LEVEL | 日志级别 | INFO |
| DEBUG | 调试模式 | False |
| TIMEZONE | 时区 | Asia/Shanghai |
| SECRET_KEY | 会话密钥，用于 FastAPI SessionMiddleware | change-me |
| ADMIN_USERNAME | 登录用户名 | admin |
| ADMIN_PASSWORD | 登录密码 | admin123 |

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)

## 联系方式

- 项目主页: <repository-url>
- 问题反馈: <repository-url>/issues
- 文档: [docs/prd.md](docs/prd.md)

## 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [SQLModel](https://sqlmodel.tiangolo.com/) - 优雅的 ORM
- [CoreDNS](https://coredns.io/) - 灵活的 DNS 服务器
- [TailwindCSS](https://tailwindcss.com/) - 实用优先的 CSS 框架
- [DaisyUI](https://daisyui.com/) - 美观的组件库
