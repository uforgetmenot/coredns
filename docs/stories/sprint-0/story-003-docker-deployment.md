# Story-003: Docker 容器化和部署配置

## 基本信息
- **故事ID**: Story-003
- **所属Sprint**: Sprint 0
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Done

## 用户故事
**As a** 运维工程师
**I want** 使用 Docker Compose 一键部署 CoreDNS 和管理工具
**So that** 可以快速在任何环境中部署和运行整个系统

## 背景描述
为了简化部署流程，需要将 CoreDNS Manager 容器化，并与现有的 CoreDNS 容器一起通过 Docker Compose 编排。两个容器需要共享 Corefile 文件，Manager 需要访问 Docker Socket 以重载 CoreDNS。

## 验收标准

- [x] AC1: Dockerfile 已创建
  - 基于 Python 3.11-slim 镜像
  - 安装 Poetry 并配置依赖
  - 正确设置工作目录和文件权限
  - 暴露 8000 端口
  - 使用 Uvicorn 启动应用

- [x] AC2: .dockerignore 已配置
  - 排除不必要的文件（`__pycache__`, `.git`, `*.pyc`, `data/db/*` 等）
  - 减小镜像体积

- [x] AC3: docker-compose.yml 已创建
  - 包含 `coredns` 服务（基于现有配置）
  - 包含 `coredns-manager` 服务
  - 配置 Volume 共享（Corefile, 数据库目录）
  - 配置网络（bridge 网络）
  - 配置环境变量

- [x] AC4: Volume 映射正确配置
  - `./data/Corefile` 同时挂载到两个容器
  - `./data/db` 挂载到 Manager 容器（数据库持久化）
  - `/var/run/docker.sock` 只读挂载到 Manager（用于控制 CoreDNS）

- [x] AC5: 网络配置正确
  - 两个容器在同一网络中
  - CoreDNS 暴露 53 端口（UDP/TCP）
  - Manager 暴露 8000 端口

- [x] AC6: 环境变量配置
  - 创建 `.env.docker` 示例文件
  - 所有配置通过环境变量传递
  - 数据库路径、Corefile 路径、容器名称等可配置

- [x] AC7: 部署文档已更新
  - README.md 包含 Docker 部署步骤
  - 说明如何启动/停止服务
  - 说明如何查看日志
  - 说明如何备份数据

- [x] AC8: 应用可以通过 Docker Compose 成功启动
  - 运行 `docker-compose up -d` 成功启动两个容器
  - Manager 容器可以访问 Corefile
  - Manager 容器可以通过 Docker Socket 控制 CoreDNS
  - 访问 `http://localhost:8000/health` 返回正常

## 技术实现要点

### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install poetry==1.7.1

# 复制依赖文件
COPY pyproject.toml poetry.lock ./

# 安装依赖（不创建虚拟环境）
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

# 复制应用代码
COPY app/ ./app/

# 创建数据目录
RUN mkdir -p /app/data/db

# 设置时区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. docker-compose.yml
```yaml
version: "3.8"

services:
  coredns:
    image: registry.k8s.io/coredns/coredns:v1.11.3
    container_name: coredns
    restart: always
    volumes:
      - ./data/Corefile:/Corefile
    ports:
      - "53:53/udp"
      - "53:53/tcp"
    networks:
      - coredns-net
    command: -conf /Corefile
    environment:
      - TZ=Asia/Shanghai
    sysctls:
      net.core.somaxconn: 4000
    ulimits:
      nofile:
        soft: 65535
        hard: 65535
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  coredns-manager:
    build: .
    container_name: coredns-manager
    restart: always
    depends_on:
      - coredns
    volumes:
      - ./data/Corefile:/app/data/Corefile
      - ./data/db:/app/data/db
      - /var/run/docker.sock:/var/run/docker.sock:ro
    ports:
      - "8000:8000"
    networks:
      - coredns-net
    environment:
      - TZ=Asia/Shanghai
      - DATABASE_URL=sqlite:///app/data/db/coredns.db
      - COREFILE_PATH=/app/data/Corefile
      - COREDNS_CONTAINER_NAME=coredns
      - LOG_LEVEL=INFO
      - DEBUG=False
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  coredns-net:
    driver: bridge

volumes:
  coredns-data:
    driver: local
```

### 3. .dockerignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Git
.git/
.gitignore

# Documentation
docs/
*.md

# Data
data/db/*
!data/db/.gitkeep

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# Other
.env
.env.*
!.env.example
```

### 4. 启动脚本（scripts/start.sh）
```bash
#!/bin/bash
set -e

echo "🚀 Starting CoreDNS Manager..."

# 创建必要的目录
mkdir -p data/db

# 检查 Corefile 是否存在
if [ ! -f "data/Corefile" ]; then
    echo "❌ data/Corefile not found!"
    echo "Please copy your Corefile to data/Corefile"
    exit 1
fi

# 启动服务
docker-compose up -d

echo "✅ Services started successfully!"
echo ""
echo "📊 Access the following URLs:"
echo "  - CoreDNS Manager: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Check logs with: docker-compose logs -f"
```

### 5. 更新 README.md 部署章节
```markdown
## Docker 部署

### 前置要求
- Docker Engine 20.10+
- Docker Compose 2.0+

### 快速启动

1. 克隆项目
\`\`\`bash
git clone <repository-url>
cd coredns
\`\`\`

2. 准备配置文件
\`\`\`bash
# 复制现有的 Corefile
cp docker/Corefile data/Corefile

# 创建环境变量文件（可选）
cp .env.example .env
\`\`\`

3. 启动服务
\`\`\`bash
docker-compose up -d
\`\`\`

4. 验证服务
\`\`\`bash
# 检查容器状态
docker-compose ps

# 检查健康状态
curl http://localhost:8000/health

# 查看日志
docker-compose logs -f coredns-manager
\`\`\`

### 常用命令

\`\`\`bash
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec coredns-manager bash

# 重建镜像
docker-compose build --no-cache
\`\`\`
```

## 依赖关系
- **前置依赖**:
  - Story-001 (需要项目结构和 pyproject.toml)
  - Story-002 (需要数据库模型，以验证容器内数据库操作)
- **后置依赖**:
  - Story-011 (CoreDNS 重载需要 Docker Socket 访问)

## 测试用例

### 测试场景 1: Docker 镜像构建
```bash
# 构建镜像
docker build -t coredns-manager:test .

# 验证镜像大小（应该 < 500MB）
docker images coredns-manager:test

# 验证镜像启动
docker run --rm -p 8000:8000 coredns-manager:test
```

### 测试场景 2: Docker Compose 启动
```bash
# 启动服务
docker-compose up -d

# 验证容器运行
docker-compose ps

# 验证健康检查
docker inspect coredns-manager | grep Health -A 10

# 停止服务
docker-compose down
```

### 测试场景 3: Volume 挂载验证
```bash
# 进入 Manager 容器
docker-compose exec coredns-manager bash

# 验证 Corefile 可访问
cat /app/data/Corefile

# 验证数据库目录可写
touch /app/data/db/test.txt

# 验证 Docker Socket 可访问
ls -la /var/run/docker.sock
```

### 测试场景 4: 容器间通信
```python
# tests/test_docker.py
import docker

def test_coredns_container_accessible():
    """测试可以通过 Docker API 访问 CoreDNS 容器"""
    client = docker.from_env()

    # 获取 CoreDNS 容器
    container = client.containers.get("coredns")

    assert container.status == "running"
    assert "coredns" in container.name
```

## 完成定义 (Definition of Done)
- [x] Dockerfile 已创建并优化
- [x] docker-compose.yml 已创建并测试
- [x] .dockerignore 已配置
- [x] 所有验收标准已满足
- [x] 使用 `docker-compose up -d` 可以成功启动
- [x] 两个容器健康检查通过
- [x] Manager 可以访问共享的 Corefile
- [x] Manager 可以通过 Docker Socket 查询 CoreDNS 容器状态
- [x] README.md 部署文档已更新
- [ ] 代码已合并到 `develop` 分支

## 参考资料
- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 官方文档](https://docs.docker.com/compose/)
- [Docker Python SDK](https://docker-py.readthedocs.io/)
- [CoreDNS Docker 镜像](https://github.com/coredns/coredns/tree/master/docker)

## 备注
- Docker Socket 挂载需要谨慎，只给予只读权限（`:ro`）
- 考虑为生产环境添加资源限制（memory, cpu）
- 可以考虑使用多阶段构建进一步减小镜像体积
- 建议配置日志轮转避免日志文件过大

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
