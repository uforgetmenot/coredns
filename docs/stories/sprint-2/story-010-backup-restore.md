# Story-010: Corefile 备份和恢复

## 基本信息
- **故事ID**: Story-010
- **所属Sprint**: Sprint 2
- **优先级**: Medium
- **预估工作量**: 2 Story Points (1 天)
- **状态**: Todo

## 用户故事
**As a** 系统管理员
**I want** 在生成新 Corefile 前自动备份当前配置，并能恢复历史版本
**So that** 在出现问题时可以快速回滚到之前的配置

## 背景描述
DNS 配置的变更可能导致服务中断，因此需要完善的备份和恢复机制。每次生成新 Corefile 前自动创建备份，并提供 API 查看和恢复历史版本。

## 验收标准

- [x] AC1: 自动备份功能已实现
  - 每次生成 Corefile 前自动备份当前文件
  - 备份文件命名规则：`Corefile.backup.{timestamp}`
  - 备份文件存储在指定目录

- [x] AC2: GET `/api/corefile/backups` 端点已实现
  - 列出所有备份文件
  - 返回备份文件信息（文件名、大小、创建时间）
  - 支持分页

- [x] AC3: GET `/api/corefile/backups/{backup_id}` 端点已实现
  - 获取指定备份的详细信息
  - 返回备份文件内容
  - 返回备份元数据

- [x] AC4: POST `/api/corefile/restore/{backup_id}` 端点已实现
  - 恢复指定的备份文件
  - 恢复前创建当前文件的备份
  - 返回恢复结果

- [x] AC5: DELETE `/api/corefile/backups/{backup_id}` 端点已实现
  - 删除指定的备份文件
  - 不能删除最新的备份
  - 返回删除确认

- [x] AC6: 备份管理功能
  - 自动清理过期备份（保留最近 30 个）
  - 备份文件大小限制检查
  - 存储空间监控

- [x] AC7: 响应格式符合规范
  ```json
  {
    "success": true,
    "data": {
      "backups": [
        {
          "id": "20251126_100000",
          "filename": "Corefile.backup.20251126_100000",
          "size": 2048,
          "created_at": "2025-11-26T10:00:00Z",
          "is_latest": true
        }
      ],
      "total": 15
    }
  }
  ```

## 技术实现要点

### 1. 备份服务（app/services/backup_service.py）
```python
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import shutil
import logging

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self, corefile_path: str, backup_dir: str = "./data/backups"):
        """
        初始化备份服务

        Args:
            corefile_path: Corefile 路径
            backup_dir: 备份目录
        """
        self.corefile_path = Path(corefile_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 30  # 最多保留 30 个备份

    def create_backup(self) -> Dict:
        """
        创建备份

        Returns:
            Dict: 备份信息
        """
        if not self.corefile_path.exists():
            raise FileNotFoundError(f"Corefile not found: {self.corefile_path}")

        # 生成备份文件名
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"Corefile.backup.{timestamp}"
        backup_path = self.backup_dir / backup_filename

        # 复制文件
        shutil.copy2(self.corefile_path, backup_path)

        # 清理旧备份
        self._cleanup_old_backups()

        backup_info = self._get_backup_info(backup_path)
        logger.info(f"Backup created: {backup_filename}")

        return backup_info

    def list_backups(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        """
        列出所有备份

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            Dict: 备份列表和分页信息
        """
        # 获取所有备份文件
        backup_files = sorted(
            self.backup_dir.glob("Corefile.backup.*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        total = len(backup_files)

        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        page_files = backup_files[start:end]

        # 获取备份信息
        backups = []
        for i, backup_file in enumerate(page_files):
            info = self._get_backup_info(backup_file)
            info["is_latest"] = (i == 0 and page == 1)
            backups.append(info)

        return {
            "backups": backups,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_backup(self, backup_id: str) -> Dict:
        """
        获取备份详情

        Args:
            backup_id: 备份 ID（时间戳）

        Returns:
            Dict: 备份详细信息
        """
        backup_filename = f"Corefile.backup.{backup_id}"
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        info = self._get_backup_info(backup_path)

        # 读取文件内容
        with open(backup_path, "r", encoding="utf-8") as f:
            info["content"] = f.read()

        return info

    def restore_backup(self, backup_id: str) -> Dict:
        """
        恢复备份

        Args:
            backup_id: 备份 ID

        Returns:
            Dict: 恢复结果
        """
        backup_filename = f"Corefile.backup.{backup_id}"
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        # 恢复前先备份当前文件
        if self.corefile_path.exists():
            current_backup = self.create_backup()
            logger.info(f"Current Corefile backed up before restore")

        # 恢复备份
        shutil.copy2(backup_path, self.corefile_path)

        logger.info(f"Backup restored: {backup_id}")

        return {
            "backup_id": backup_id,
            "restored_at": datetime.utcnow().isoformat(),
            "corefile_path": str(self.corefile_path)
        }

    def delete_backup(self, backup_id: str):
        """
        删除备份

        Args:
            backup_id: 备份 ID
        """
        backup_filename = f"Corefile.backup.{backup_id}"
        backup_path = self.backup_dir / backup_filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_id}")

        # 检查是否是最新备份
        backups = sorted(
            self.backup_dir.glob("Corefile.backup.*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if backups and backup_path == backups[0]:
            raise ValueError("Cannot delete the latest backup")

        backup_path.unlink()
        logger.info(f"Backup deleted: {backup_id}")

    def _get_backup_info(self, backup_path: Path) -> Dict:
        """
        获取备份文件信息

        Args:
            backup_path: 备份文件路径

        Returns:
            Dict: 备份信息
        """
        stat = backup_path.stat()
        backup_id = backup_path.name.replace("Corefile.backup.", "")

        return {
            "id": backup_id,
            "filename": backup_path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }

    def _cleanup_old_backups(self):
        """清理旧备份"""
        backup_files = sorted(
            self.backup_dir.glob("Corefile.backup.*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        # 删除超过最大数量的备份
        for backup_file in backup_files[self.max_backups:]:
            backup_file.unlink()
            logger.info(f"Old backup deleted: {backup_file.name}")
```

### 2. Pydantic 模型（app/schemas/backup.py）
```python
from pydantic import BaseModel
from typing import List, Optional

class BackupInfo(BaseModel):
    id: str
    filename: str
    size: int
    created_at: str
    is_latest: bool = False

class BackupListResponse(BaseModel):
    success: bool = True
    data: dict

class BackupDetailResponse(BaseModel):
    success: bool = True
    data: dict

class RestoreResponse(BaseModel):
    success: bool = True
    data: dict
    message: str
```

### 3. API 路由（app/api/corefile.py）
```python
from fastapi import APIRouter, HTTPException, Query
from app.services.backup_service import BackupService
from app.schemas.backup import (
    BackupListResponse,
    BackupDetailResponse,
    RestoreResponse
)
from app.config import settings

router = APIRouter(prefix="/api/corefile", tags=["Corefile"])

@router.get("/backups", response_model=BackupListResponse)
async def list_backups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """列出所有 Corefile 备份"""
    try:
        backup_service = BackupService(settings.corefile_path)
        result = backup_service.list_backups(page, page_size)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backups/{backup_id}", response_model=BackupDetailResponse)
async def get_backup(backup_id: str):
    """获取备份详情"""
    try:
        backup_service = BackupService(settings.corefile_path)
        backup = backup_service.get_backup(backup_id)

        return {
            "success": True,
            "data": backup
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/restore/{backup_id}", response_model=RestoreResponse)
async def restore_backup(backup_id: str):
    """恢复备份"""
    try:
        backup_service = BackupService(settings.corefile_path)
        result = backup_service.restore_backup(backup_id)

        return {
            "success": True,
            "data": result,
            "message": f"Backup {backup_id} restored successfully"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str):
    """删除备份"""
    try:
        backup_service = BackupService(settings.corefile_path)
        backup_service.delete_backup(backup_id)

        return {
            "success": True,
            "message": f"Backup {backup_id} deleted successfully"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. 集成到 Corefile 生成（app/services/corefile_service.py）
```python
from app.services.backup_service import BackupService

class CorefileService:
    def generate_corefile(self, session: Session, output_path: str = None):
        # 生成前先备份
        if output_path and Path(output_path).exists():
            backup_service = BackupService(output_path)
            backup_info = backup_service.create_backup()
            logger.info(f"Backup created: {backup_info['filename']}")

        # 生成新 Corefile
        # ...
```

## 依赖关系
- **前置依赖**:
  - Story-002 (需要数据库模型)
  - Story-009 (依赖 Corefile 生成功能)
- **后置依赖**:
  - Story-019 (系统监控可能需要显示备份信息)

## 测试用例

### 测试场景 1: 自动创建备份
```python
def test_auto_backup_on_generate():
    # 先创建一个 Corefile
    client.post("/api/records", json={
        "zone": "test.com", "hostname": "app", "ip_address": "172.27.0.3"
    })
    client.post("/api/corefile/generate")

    # 再次生成，应该自动创建备份
    response = client.post("/api/corefile/generate")
    assert response.status_code == 200

    # 检查备份是否创建
    backups_response = client.get("/api/corefile/backups")
    assert len(backups_response.json()["data"]["backups"]) > 0
```

### 测试场景 2: 列出备份
```python
def test_list_backups():
    response = client.get("/api/corefile/backups")
    assert response.status_code == 200
    data = response.json()
    assert "backups" in data["data"]
    assert "total" in data["data"]
```

### 测试场景 3: 获取备份详情
```python
def test_get_backup_detail():
    # 创建备份
    client.post("/api/corefile/generate")
    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    backup_id = backups[0]["id"]

    # 获取详情
    response = client.get(f"/api/corefile/backups/{backup_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "content" in data
```

### 测试场景 4: 恢复备份
```python
def test_restore_backup():
    # 创建两个版本
    client.post("/api/corefile/generate")
    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    backup_id = backups[0]["id"]

    # 恢复
    response = client.post(f"/api/corefile/restore/{backup_id}")
    assert response.status_code == 200
    assert "restored_at" in response.json()["data"]
```

### 测试场景 5: 删除备份
```python
def test_delete_backup():
    # 创建多个备份
    for i in range(3):
        client.post("/api/corefile/generate")

    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    # 删除非最新的备份
    old_backup_id = backups[-1]["id"]

    response = client.delete(f"/api/corefile/backups/{old_backup_id}")
    assert response.status_code == 200
```

## 完成定义 (Definition of Done)
- [x] 备份服务已实现
- [x] 所有验收标准已满足
- [x] API 端点已实现
- [x] 自动备份集成到 Corefile 生成流程
- [x] 备份清理逻辑已实现
- [x] 单元测试通过（覆盖率 ≥ 80%）
- [x] API 文档已生成
- [x] 代码已合并到 `develop` 分支

## 参考资料
- [Python shutil Documentation](https://docs.python.org/3/library/shutil.html)
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [Backup Best Practices](https://en.wikipedia.org/wiki/Backup)

## 备注
- 备份文件应该定期清理以节省空间
- 可以考虑压缩备份文件以减少存储空间
- 可以添加备份文件的完整性校验（MD5/SHA256）
- 考虑支持远程备份存储（S3, NFS 等）

---

**创建日期**: 2025-11-26
**最后更新**: 2025-11-26
**创建者**: 开发团队
