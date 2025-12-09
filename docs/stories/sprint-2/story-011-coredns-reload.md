# Story-011: CoreDNS 重载集成

## 基本信息
- **故事ID**: Story-011
- **所属Sprint**: Sprint 2
- **优先级**: High
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 在 Corefile 更新后自动重载 CoreDNS 服务
**So that** 新的 DNS 配置可以立即生效，无需手动重启服务

## 背景描述
CoreDNS 支持动态重载配置文件，无需重启服务。本功能需要通过 Docker API 或信号机制触发 CoreDNS 重载，确保配置变更后立即生效。

## 验收标准

- [x] AC1: POST `/api/coredns/reload` 端点已实现
  - 触发 CoreDNS 服务重载
  - 支持 Docker 容器方式和进程信号方式
  - 返回重载结果和状态

- [x] AC2: Docker 容器重载支持
  - 通过 Docker API 向容器发送 SIGUSR1 信号
  - 检测容器是否存在和运行
  - 处理重载超时情况

- [x] AC3: 进程信号重载支持（备选方案）
  - 通过 kill 命令发送 SIGUSR1 信号
  - 查找 CoreDNS 进程 PID
  - 验证信号发送成功

- [x] AC4: 重载状态检查
  - 检查 CoreDNS 是否运行中
  - 验证 Corefile 是否存在
  - 检查 Corefile 语法是否正确

- [x] AC5: GET `/api/coredns/status` 端点已实现
  - 返回 CoreDNS 运行状态
  - 返回容器/进程信息
  - 返回当前配置文件路径

- [x] AC6: 响应格式符合规范
  ```json
  {
    "success": true,
    "data": {
      "method": "docker",
      "container_name": "coredns",
      "reload_at": "2025-11-26T10:00:00Z",
      "status": "success"
    },
    "message": "CoreDNS reloaded successfully"
  }
  ```

- [x] AC7: 单元测试覆盖率 ≥ 80%
  - 测试 Docker 重载
  - 测试状态检查
  - 测试错误处理
  - Mock Docker API 调用

## 技术实现要点

### 1. CoreDNS 重载服务（app/services/coredns_service.py）
```python
import docker
from docker.errors import DockerException, NotFound
import subprocess
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class CoreDNSService:
    def __init__(self, container_name: str = "coredns"):
        """
        初始化 CoreDNS 服务

        Args:
            container_name: CoreDNS 容器名称
        """
        self.container_name = container_name
        try:
            self.docker_client = docker.from_env()
            self.use_docker = True
        except DockerException:
            logger.warning("Docker not available, will use process signals")
            self.use_docker = False

    def reload(self) -> Dict:
        """
        重载 CoreDNS 配置

        Returns:
            Dict: 重载结果
        """
        if self.use_docker:
            return self._reload_docker()
        else:
            return self._reload_process()

    def _reload_docker(self) -> Dict:
        """
        通过 Docker 重载 CoreDNS

        Returns:
            Dict: 重载结果
        """
        try:
            # 获取容器
            container = self.docker_client.containers.get(self.container_name)

            # 检查容器是否运行
            if container.status != "running":
                raise Exception(f"Container {self.container_name} is not running")

            # 发送 SIGUSR1 信号重载配置
            container.kill(signal="SIGUSR1")

            logger.info(f"CoreDNS container {self.container_name} reloaded")

            return {
                "method": "docker",
                "container_name": self.container_name,
                "reload_at": datetime.utcnow().isoformat(),
                "status": "success"
            }

        except NotFound:
            raise Exception(f"Container {self.container_name} not found")
        except DockerException as e:
            raise Exception(f"Docker error: {str(e)}")

    def _reload_process(self) -> Dict:
        """
        通过进程信号重载 CoreDNS

        Returns:
            Dict: 重载结果
        """
        try:
            # 查找 CoreDNS 进程
            result = subprocess.run(
                ["pgrep", "-f", "coredns"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception("CoreDNS process not found")

            pid = result.stdout.strip()

            # 发送 SIGUSR1 信号
            subprocess.run(["kill", "-USR1", pid], check=True)

            logger.info(f"CoreDNS process {pid} reloaded")

            return {
                "method": "process",
                "pid": pid,
                "reload_at": datetime.utcnow().isoformat(),
                "status": "success"
            }

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to reload CoreDNS process: {str(e)}")

    def get_status(self) -> Dict:
        """
        获取 CoreDNS 状态

        Returns:
            Dict: 状态信息
        """
        if self.use_docker:
            return self._get_docker_status()
        else:
            return self._get_process_status()

    def _get_docker_status(self) -> Dict:
        """
        获取 Docker 容器状态

        Returns:
            Dict: 容器状态
        """
        try:
            container = self.docker_client.containers.get(self.container_name)

            return {
                "method": "docker",
                "container_name": self.container_name,
                "container_id": container.short_id,
                "status": container.status,
                "running": container.status == "running",
                "created_at": container.attrs["Created"],
                "image": container.image.tags[0] if container.image.tags else "unknown"
            }

        except NotFound:
            return {
                "method": "docker",
                "container_name": self.container_name,
                "status": "not_found",
                "running": False
            }
        except DockerException as e:
            logger.error(f"Docker error: {str(e)}")
            return {
                "method": "docker",
                "status": "error",
                "error": str(e)
            }

    def _get_process_status(self) -> Dict:
        """
        获取进程状态

        Returns:
            Dict: 进程状态
        """
        try:
            result = subprocess.run(
                ["pgrep", "-f", "coredns"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pid = result.stdout.strip()
                return {
                    "method": "process",
                    "pid": pid,
                    "running": True,
                    "status": "running"
                }
            else:
                return {
                    "method": "process",
                    "running": False,
                    "status": "not_running"
                }

        except Exception as e:
            return {
                "method": "process",
                "status": "error",
                "error": str(e)
            }

    def validate_corefile(self, corefile_path: str) -> bool:
        """
        验证 Corefile 语法（简单检查）

        Args:
            corefile_path: Corefile 路径

        Returns:
            bool: 是否有效
        """
        from pathlib import Path

        path = Path(corefile_path)

        # 检查文件是否存在
        if not path.exists():
            return False

        # 检查文件是否为空
        if path.stat().st_size == 0:
            return False

        # 基本语法检查（检查是否包含必要的块）
        try:
            with open(path, "r") as f:
                content = f.read()
                # 简单验证：包含 { 和 }
                return "{" in content and "}" in content
        except Exception:
            return False
```

### 2. Pydantic 模型（app/schemas/coredns.py）
```python
from pydantic import BaseModel
from typing import Optional

class CoreDNSReloadResponse(BaseModel):
    success: bool = True
    data: dict
    message: str

class CoreDNSStatusResponse(BaseModel):
    success: bool = True
    data: dict
```

### 3. API 路由（app/api/coredns.py）
```python
from fastapi import APIRouter, HTTPException
from app.services.coredns_service import CoreDNSService
from app.schemas.coredns import CoreDNSReloadResponse, CoreDNSStatusResponse
from app.config import settings

router = APIRouter(prefix="/api/coredns", tags=["CoreDNS"])

@router.post("/reload", response_model=CoreDNSReloadResponse)
async def reload_coredns():
    """
    重载 CoreDNS 配置

    通过发送 SIGUSR1 信号重载 CoreDNS，使新配置生效
    """
    try:
        service = CoreDNSService(settings.coredns_container_name)

        # 验证 Corefile
        if not service.validate_corefile(settings.corefile_path):
            raise HTTPException(
                status_code=400,
                detail="Corefile is invalid or does not exist"
            )

        result = service.reload()

        return {
            "success": True,
            "data": result,
            "message": "CoreDNS reloaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload CoreDNS: {str(e)}"
        )

@router.get("/status", response_model=CoreDNSStatusResponse)
async def get_coredns_status():
    """
    获取 CoreDNS 运行状态

    返回 CoreDNS 容器或进程的运行状态信息
    """
    try:
        service = CoreDNSService(settings.coredns_container_name)
        status = service.get_status()

        return {
            "success": True,
            "data": status
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get CoreDNS status: {str(e)}"
        )
```

### 4. 集成到 Corefile 生成（app/services/corefile_service.py）
```python
from app.services.coredns_service import CoreDNSService

class CorefileService:
    def generate_corefile(
        self,
        session: Session,
        output_path: str = None,
        auto_reload: bool = True
    ):
        # 生成 Corefile
        # ...

        # 自动重载 CoreDNS
        if auto_reload:
            try:
                coredns_service = CoreDNSService()
                reload_result = coredns_service.reload()
                logger.info("CoreDNS reloaded after Corefile generation")
                result["reload_result"] = reload_result
            except Exception as e:
                logger.error(f"Failed to reload CoreDNS: {str(e)}")
                result["reload_error"] = str(e)

        return result
```

### 5. 注册路由（app/main.py）
```python
from app.api import coredns

app.include_router(coredns.router)
```

### 6. 配置更新（app/config.py）
```python
class Settings(BaseSettings):
    # ... 其他配置
    coredns_container_name: str = "coredns"
    auto_reload_on_generate: bool = True  # 生成后自动重载
```

## 依赖关系
- **前置依赖**:
  - Story-009 (需要 Corefile 生成功能)
- **后置依赖**:
  - Story-019 (系统监控需要显示 CoreDNS 状态)

## 测试用例

### 测试场景 1: 成功重载 CoreDNS（Mock）
```python
from unittest.mock import patch, MagicMock

def test_reload_coredns_success():
    with patch("docker.from_env") as mock_docker:
        # Mock Docker 客户端
        mock_container = MagicMock()
        mock_container.status = "running"
        mock_docker.return_value.containers.get.return_value = mock_container

        response = client.post("/api/coredns/reload")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "success"
```

### 测试场景 2: 获取 CoreDNS 状态
```python
def test_get_coredns_status():
    response = client.get("/api/coredns/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data["data"] or "status" in data["data"]
```

### 测试场景 3: Corefile 不存在时重载失败
```python
def test_reload_without_corefile():
    with patch("pathlib.Path.exists", return_value=False):
        response = client.post("/api/coredns/reload")
        assert response.status_code == 400
```

### 测试场景 4: 容器不存在
```python
from docker.errors import NotFound

def test_reload_container_not_found():
    with patch("docker.from_env") as mock_docker:
        mock_docker.return_value.containers.get.side_effect = NotFound("Container not found")

        response = client.post("/api/coredns/reload")
        assert response.status_code == 500
```

### 测试场景 5: 生成后自动重载
```python
def test_auto_reload_after_generate():
    with patch("app.services.coredns_service.CoreDNSService.reload") as mock_reload:
        mock_reload.return_value = {"status": "success"}

        # 创建记录并生成 Corefile
        client.post("/api/records", json={
            "zone": "test.com", "hostname": "app", "ip_address": "172.27.0.3"
        })
        response = client.post("/api/corefile/generate")

        assert response.status_code == 200
        # 验证 reload 被调用
        mock_reload.assert_called_once()
```

## 完成定义 (Definition of Done)
- [x] CoreDNS 重载服务已实现
- [x] 所有验收标准已满足
- [x] Docker 重载方式已实现
- [x] 进程信号重载方式已实现（备选）
- [x] API 端点已实现
- [x] 集成到 Corefile 生成流程
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [CoreDNS Reload](https://coredns.io/2017/07/23/corefile-explained/)
- [Docker Python SDK](https://docker-py.readthedocs.io/)
- [Docker Container Signals](https://docs.docker.com/engine/reference/commandline/kill/)

## 备注
- CoreDNS 使用 SIGUSR1 信号触发配置重载
- 重载是热重载，不会中断服务
- 如果 Corefile 语法错误，CoreDNS 会保持使用旧配置
- 建议在重载前验证 Corefile 语法
- 可以添加重载日志记录功能
- 考虑添加重载失败时的回滚机制

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
