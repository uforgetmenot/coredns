"""Tests for Corefile generation, preview, and backup APIs"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select

from app.config import settings
from app.database import get_session
from app.main import application
from app.models.dns_record import DNSRecord
from app.services.corefile_service import CorefileService
from app.services.backup_service import BackupService


@pytest.fixture(scope="function")
def session(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture(scope="function")
def client(session, tmp_path, monkeypatch):
    def get_session_override():
        return session

    application.dependency_overrides[get_session] = get_session_override
    monkeypatch.setattr(settings, "corefile_path", str(tmp_path / "Corefile"))
    monkeypatch.setattr(settings, "corefile_backup_dir", str(tmp_path / "backups"))

    client = TestClient(application)
    yield client
    application.dependency_overrides.clear()


def _create_record(session: Session, zone: str, hostname: str, ip_address: str, status: str = "active"):
    record = DNSRecord(zone=zone, hostname=hostname, ip_address=ip_address, record_type="A", status=status)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def _ensure_record_exists(session: Session):
    exists = session.exec(select(DNSRecord)).first()
    if not exists:
        _create_record(session, "backups.com", "host", "10.0.0.10")


def _create_backups(client: TestClient, session: Session, num_backups: int = 1):
    _ensure_record_exists(session)
    client.post("/api/corefile/generate")
    for _ in range(num_backups):
        client.post("/api/corefile/generate")


def test_generate_corefile_success(client, session):
    _create_record(session, "seadee.com.cn", "app", "172.27.0.3")
    _create_record(session, "seadee.com.cn", "web", "172.27.0.4")

    response = client.post("/api/corefile/generate")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["stats"]["total_zones"] == 1
    assert data["stats"]["total_records"] == 2
    assert "app.seadee.com.cn" in data["content"]


def test_preview_corefile_returns_content(client):
    response = client.get("/api/corefile/preview")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "content" in data
    assert "generated_at" in data


def test_zone_grouping(client, session):
    _create_record(session, "zone1.com", "app", "10.0.0.1")
    _create_record(session, "zone2.com", "web", "10.0.0.2")

    response = client.post("/api/corefile/generate")
    content = response.json()["data"]["content"]
    assert "zone1.com" in content
    assert "zone2.com" in content


def test_only_active_records(client, session):
    _create_record(session, "test.com", "active", "10.0.0.3", status="active")
    _create_record(session, "test.com", "inactive", "10.0.0.4", status="inactive")

    response = client.post("/api/corefile/generate")
    content = response.json()["data"]["content"]
    assert "active.test.com" in content
    assert "inactive.test.com" not in content


def test_corefile_service_writes_file(session, tmp_path):
    _create_record(session, "write.com", "srv", "10.1.1.1")
    output_path = tmp_path / "Corefile"

    service = CorefileService()
    result = service.generate_corefile(session=session, output_path=str(output_path))

    assert output_path.exists()
    with open(output_path, "r", encoding="utf-8") as fh:
        file_content = fh.read()
    assert "write.com" in file_content
    assert result["corefile_path"] == str(output_path)


def test_auto_backup_on_generate(client, session):
    _create_backups(client, session, num_backups=1)
    response = client.get("/api/corefile/backups")
    backups = response.json()["data"]["backups"]
    assert len(backups) >= 1


def test_list_backups_endpoint(client, session):
    _create_backups(client, session, num_backups=2)
    response = client.get("/api/corefile/backups?page=1&page_size=10")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert "backups" in payload
    assert payload["total"] >= 2


def test_get_backup_detail(client, session):
    _create_backups(client, session, num_backups=1)
    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    backup_id = backups[0]["id"]

    detail = client.get(f"/api/corefile/backups/{backup_id}")
    assert detail.status_code == 200
    data = detail.json()["data"]
    assert data["id"] == backup_id
    assert "content" in data


def test_restore_backup(client, session):
    _create_backups(client, session, num_backups=1)
    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    backup_id = backups[0]["id"]
    backup_detail = client.get(f"/api/corefile/backups/{backup_id}").json()["data"]

    # Modify current Corefile content
    with open(settings.corefile_path, "w", encoding="utf-8") as fh:
        fh.write("corrupted corefile")

    restore_response = client.post(f"/api/corefile/restore/{backup_id}")
    assert restore_response.status_code == 200
    with open(settings.corefile_path, "r", encoding="utf-8") as fh:
        restored_content = fh.read()
    assert backup_detail["content"] == restored_content


def test_delete_backup(client, session):
    _create_backups(client, session, num_backups=3)
    backups = client.get("/api/corefile/backups").json()["data"]["backups"]
    assert len(backups) >= 3
    backup_to_delete = backups[-1]["id"]

    delete_response = client.delete(f"/api/corefile/backups/{backup_to_delete}")
    assert delete_response.status_code == 200
    ids_after = [b["id"] for b in client.get("/api/corefile/backups").json()["data"]["backups"]]
    assert backup_to_delete not in ids_after
