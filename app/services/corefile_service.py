"""Corefile generation service"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlmodel import Session, select

from app.models.dns_record import DNSRecord
from app.config import settings
from app.services.backup_service import BackupService
from app.services.coredns_service import CoreDNSService

logger = logging.getLogger(__name__)


class CorefileService:
    """Service responsible for rendering/writing Corefile"""

    def __init__(
        self,
        template_dir: str = "app/templates",
        template_name: str = "Corefile.j2",
        backup_dir: str | None = None,
    ):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template(template_name)
        self.backup_dir = backup_dir or settings.corefile_backup_dir

    def generate_corefile(
        self,
        session: Session,
        output_path: str | None = None,
        auto_reload: bool = True,
    ) -> Dict:
        """Generate Corefile content and optionally write to disk"""

        records: List[DNSRecord] = session.exec(
            select(DNSRecord).where(DNSRecord.status == "active")
        ).all()

        zones = self._group_records_by_zone(records)
        generated_at = datetime.now(timezone.utc).isoformat()
        content = self.template.render(zones=zones, generated_at=generated_at)

        stats = {
            "total_zones": len(zones),
            "total_records": len(records),
            "active_records": len(records),
        }

        result: Dict = {
            "content": content,
            "stats": stats,
            "generated_at": generated_at,
        }

        if output_path:
            file_path = Path(output_path)
            if file_path.exists():
                backup_service = BackupService(
                    corefile_path=output_path,
                    backup_dir=self.backup_dir,
                )
                backup_service.create_backup()
            self._write_corefile(output_path, content)
            result["corefile_path"] = output_path

            if auto_reload:
                try:
                    reload_result = CoreDNSService().reload()
                    result["reload_result"] = reload_result
                except Exception as exc:  # pragma: no cover - system dependent
                    logger.error("Failed to reload CoreDNS: %s", exc)
                    result["reload_error"] = str(exc)

        return result

    def _group_records_by_zone(self, records: List[DNSRecord]) -> List[Dict]:
        zones: Dict[str, Dict] = {}
        for record in records:
            zones.setdefault(record.zone, {"name": record.zone, "records": []})[
                "records"
            ].append(record)
        return list(zones.values())

    def _write_corefile(self, path: str, content: str) -> None:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            logger.info("Corefile written to %s", path)
        except Exception as exc:  # pragma: no cover - file errors
            logger.error("Failed to write Corefile: %s", exc)
            raise

    def validate_corefile(self, content: str) -> bool:
        required_blocks = ["{", "}", "hosts"]
        return all(block in content for block in required_blocks)
