"""Corefile backup management service"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from app.config import settings

logger = logging.getLogger(__name__)


class BackupService:
    """Handles filesystem-based Corefile backups"""

    def __init__(
        self,
        corefile_path: str,
        backup_dir: str | None = None,
        max_backups: int | None = None,
        max_backup_size_bytes: int | None = None,
    ):
        self.corefile_path = Path(corefile_path)
        self.backup_dir = Path(backup_dir or settings.corefile_backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups or settings.max_corefile_backups
        self.max_backup_size_bytes = max_backup_size_bytes or settings.max_backup_size_bytes

    def create_backup(self) -> Dict:
        if not self.corefile_path.exists():
            raise FileNotFoundError(f"Corefile not found: {self.corefile_path}")

        size = self.corefile_path.stat().st_size
        if size > self.max_backup_size_bytes:
            raise ValueError("Corefile exceeds maximum backup size limit")

        if not self._has_enough_space(size):
            raise OSError("Insufficient disk space for backup")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"Corefile.backup.{timestamp}"
        backup_path = self.backup_dir / backup_filename

        shutil.copy2(self.corefile_path, backup_path)
        self._cleanup_old_backups()

        info = self._get_backup_info(backup_path)
        logger.info("Backup created: %s", backup_filename)
        return info

    def list_backups(self, page: int = 1, page_size: int = 20) -> Dict:
        files = self._sorted_backups()
        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        page_files = files[start:end]

        backups: List[Dict] = []
        for idx, file in enumerate(page_files):
            info = self._get_backup_info(file)
            info["is_latest"] = idx == 0 and page == 1
            backups.append(info)

        return {
            "backups": backups,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_backup(self, backup_id: str) -> Dict:
        backup_path = self._backup_path(backup_id)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        info = self._get_backup_info(backup_path)
        info["content"] = backup_path.read_text(encoding="utf-8")
        return info

    def restore_backup(self, backup_id: str) -> Dict:
        backup_path = self._backup_path(backup_id)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        if self.corefile_path.exists():
            self.create_backup()

        self.corefile_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, self.corefile_path)
        logger.info("Backup restored: %s", backup_id)

        return {
            "backup_id": backup_id,
            "restored_at": datetime.now(timezone.utc).isoformat(),
            "corefile_path": str(self.corefile_path),
        }

    def delete_backup(self, backup_id: str) -> None:
        backup_path = self._backup_path(backup_id)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        files = self._sorted_backups()
        if files and backup_path == files[0]:
            raise ValueError("Cannot delete the latest backup")

        backup_path.unlink()
        logger.info("Backup deleted: %s", backup_id)

    def _sorted_backups(self) -> List[Path]:
        return sorted(
            self.backup_dir.glob("Corefile.backup.*"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

    def _cleanup_old_backups(self) -> None:
        files = self._sorted_backups()
        for file in files[self.max_backups :]:
            file.unlink(missing_ok=True)
            logger.info("Old backup deleted: %s", file.name)

    def _get_backup_info(self, path: Path) -> Dict:
        stat = path.stat()
        backup_id = path.name.replace("Corefile.backup.", "")
        return {
            "id": backup_id,
            "filename": path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }

    def _backup_path(self, backup_id: str) -> Path:
        return self.backup_dir / f"Corefile.backup.{backup_id}"

    def _has_enough_space(self, size: int) -> bool:
        try:
            usage = shutil.disk_usage(self.backup_dir)
            return usage.free >= size
        except Exception:  # pragma: no cover - platform-specific
            return True
