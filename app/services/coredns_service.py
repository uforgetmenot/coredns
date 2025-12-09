"""CoreDNS reload/status service"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

try:  # pragma: no cover - docker optional
    import docker
    from docker.errors import DockerException, NotFound
except Exception:  # pragma: no cover
    docker = None
    DockerException = NotFound = Exception

from app.config import settings

logger = logging.getLogger(__name__)


class CoreDNSService:
    def __init__(self, container_name: str | None = None):
        self.container_name = container_name or settings.coredns_container_name
        self.use_docker = settings.coredns_reload_method == "docker" and docker is not None
        self.docker_client = None
        if self.use_docker:
            try:
                self.docker_client = docker.from_env()
            except DockerException:  # pragma: no cover - no docker
                logger.warning("Docker not available; falling back to process mode")
                self.use_docker = False

    def reload(self) -> Dict:
        return self._reload_docker() if self.use_docker else self._reload_process()

    def _reload_docker(self) -> Dict:
        assert self.docker_client is not None
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status != "running":
                raise RuntimeError(f"Container {self.container_name} is not running")
            container.kill(signal="SIGUSR1")
            return {
                "method": "docker",
                "container_name": self.container_name,
                "reload_at": datetime.now(timezone.utc).isoformat(),
                "status": "success",
            }
        except NotFound as exc:
            raise RuntimeError(str(exc))
        except DockerException as exc:  # pragma: no cover
            raise RuntimeError(f"Docker error: {exc}")

    def _reload_process(self) -> Dict:
        pid = self._find_process()
        if not pid:
            raise RuntimeError("CoreDNS process not found")
        subprocess.run(["kill", "-USR1", pid], check=True)
        return {
            "method": "process",
            "pid": pid,
            "reload_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
        }

    def get_status(self) -> Dict:
        return self._get_docker_status() if self.use_docker else self._get_process_status()

    def _get_docker_status(self) -> Dict:
        assert self.docker_client is not None
        try:
            container = self.docker_client.containers.get(self.container_name)
            return {
                "method": "docker",
                "container_name": self.container_name,
                "container_id": container.short_id,
                "status": container.status,
                "running": container.status == "running",
            }
        except NotFound:
            return {
                "method": "docker",
                "container_name": self.container_name,
                "status": "not_found",
                "running": False,
            }
        except DockerException as exc:  # pragma: no cover
            return {"method": "docker", "status": "error", "error": str(exc)}

    def _get_process_status(self) -> Dict:
        pid = self._find_process()
        return {
            "method": "process",
            "pid": pid,
            "running": pid is not None,
            "status": "running" if pid else "not_running",
        }

    def validate_corefile(self, corefile_path: str) -> bool:
        path = Path(corefile_path)
        if not path.exists() or path.stat().st_size == 0:
            return False
        content = path.read_text(encoding="utf-8")
        return "{" in content and "}" in content

    def _find_process(self) -> str | None:
        result = subprocess.run(["pgrep", "-f", "coredns"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
        return None
