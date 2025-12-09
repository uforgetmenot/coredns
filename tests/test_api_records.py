"""
测试 DNS 记录 API
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select

from app.database import get_session
from app.main import application
from app.models.dns_record import DNSRecord


# 创建测试客户端
@pytest.fixture(scope="function")
def session():
    """创建独立的测试数据库会话"""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    database_url = f"sqlite:///{temp_db.name}"

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()
    os.unlink(temp_db.name)


@pytest.fixture(scope="function")
def client(session):
    """创建测试客户端"""

    def get_session_override():
        return session

    application.dependency_overrides[get_session] = get_session_override
    client = TestClient(application)
    yield client
    application.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_records(session):
    """创建测试数据"""
    records = [
        DNSRecord(
            zone="seadee.com.cn",
            hostname="app",
            ip_address="172.27.0.3",
            record_type="A",
            description="Application server",
            status="active",
        ),
        DNSRecord(
            zone="seadee.com.cn",
            hostname="db",
            ip_address="172.27.0.4",
            record_type="A",
            description="Database server",
            status="active",
        ),
        DNSRecord(
            zone="example.com",
            hostname="www",
            ip_address="192.168.1.1",
            record_type="A",
            description="Web server",
            status="active",
        ),
        DNSRecord(
            zone="example.com",
            hostname="mail",
            ip_address="192.168.1.2",
            record_type="A",
            description="Mail server",
            status="inactive",
        ),
        DNSRecord(
            zone="test.local",
            hostname="api",
            ip_address="10.0.0.5",
            record_type="A",
            description="API server",
            status="active",
        ),
    ]

    for record in records:
        session.add(record)
    session.commit()

    for record in records:
        session.refresh(record)

    return records


def test_list_records_basic(client, sample_records):
    """测试基本列表查询"""
    response = client.get("/api/records")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert "pagination" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 5


def test_list_records_pagination(client, sample_records):
    """测试分页功能"""
    # 测试第一页
    response = client.get("/api/records?page=1&page_size=2")
    assert response.status_code == 200

    data = response.json()
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["pages"] == 3
    assert len(data["data"]) == 2

    # 测试第二页
    response = client.get("/api/records?page=2&page_size=2")
    assert response.status_code == 200

    data = response.json()
    assert data["pagination"]["page"] == 2
    assert len(data["data"]) == 2


def test_list_records_filter_by_zone(client, sample_records):
    """测试 Zone 过滤"""
    response = client.get("/api/records?zone=seadee.com.cn")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2

    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"


def test_list_records_filter_by_status(client, sample_records):
    """测试状态过滤"""
    response = client.get("/api/records?status=active")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 4

    for record in data["data"]:
        assert record["status"] == "active"

    # 测试 inactive 状态
    response = client.get("/api/records?status=inactive")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "inactive"


def test_list_records_search(client, sample_records):
    """测试搜索功能"""
    # 搜索 hostname
    response = client.get("/api/records?search=app")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["hostname"] == "app"

    # 搜索 IP 地址
    response = client.get("/api/records?search=172.27")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 2


def test_list_records_sorting(client, sample_records):
    """测试排序功能"""
    # 按 hostname 升序
    response = client.get("/api/records?sort_by=hostname&order=asc")
    assert response.status_code == 200

    data = response.json()
    hostnames = [r["hostname"] for r in data["data"]]
    assert hostnames == sorted(hostnames)

    # 按 hostname 降序
    response = client.get("/api/records?sort_by=hostname&order=desc")
    assert response.status_code == 200

    data = response.json()
    hostnames = [r["hostname"] for r in data["data"]]
    assert hostnames == sorted(hostnames, reverse=True)


def test_list_records_combined_filters(client, sample_records):
    """测试组合过滤"""
    response = client.get("/api/records?zone=seadee.com.cn&status=active&page_size=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) == 2

    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"
        assert record["status"] == "active"


def test_list_records_empty_result(client, session):
    """测试空结果"""
    response = client.get("/api/records")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 0
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["pages"] == 0


def test_list_records_invalid_page(client, sample_records):
    """测试无效页码"""
    # 页码小于 1
    response = client.get("/api/records?page=0")
    assert response.status_code == 422  # Validation error


def test_list_records_page_size_limit(client, sample_records):
    """测试 page_size 限制"""
    # 超过最大值
    response = client.get("/api/records?page_size=200")
    assert response.status_code == 422  # Validation error


def test_list_records_invalid_order(client, sample_records):
    """测试无效的排序方向"""
    response = client.get("/api/records?order=invalid")
    assert response.status_code == 422  # Validation error


def test_list_records_response_structure(client, sample_records):
    """测试响应结构"""
    response = client.get("/api/records")
    assert response.status_code == 200

    data = response.json()

    # 验证顶层结构
    assert "success" in data
    assert "data" in data
    assert "pagination" in data

    # 验证分页结构
    pagination = data["pagination"]
    assert "total" in pagination
    assert "page" in pagination
    assert "page_size" in pagination
    assert "pages" in pagination

    # 验证记录结构
    if len(data["data"]) > 0:
        record = data["data"][0]
        assert "id" in record
        assert "zone" in record
        assert "hostname" in record
        assert "ip_address" in record
        assert "record_type" in record
        assert "status" in record
        assert "created_at" in record
        assert "updated_at" in record


def test_create_record_success(client, session):
    """测试成功创建记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "newapp",
        "ip_address": "172.27.0.50",
        "record_type": "A",
        "description": "New application server",
    }

    response = client.post("/api/records", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "DNS record created successfully"
    assert data["data"]["hostname"] == "newapp"
    assert data["data"]["zone"] == "seadee.com.cn"
    assert data["data"]["record_type"] == "A"

    stored = session.exec(
        select(DNSRecord).where(
            DNSRecord.zone == "seadee.com.cn",
            DNSRecord.hostname == "newapp",
        )
    ).first()
    assert stored is not None


def test_create_record_invalid_ip(client):
    """测试 IP 地址验证"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "invalidip",
        "ip_address": "999.999.999.999",
    }

    response = client.post("/api/records", json=payload)
    assert response.status_code == 422


def test_create_record_invalid_hostname(client):
    """测试主机名验证"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "bad@host",
        "ip_address": "172.27.0.60",
    }

    response = client.post("/api/records", json=payload)
    assert response.status_code == 422


def test_create_record_missing_fields(client):
    """测试必填字段验证"""

    payload = {
        "zone": "seadee.com.cn",
    }

    response = client.post("/api/records", json=payload)
    assert response.status_code == 422


def test_create_record_duplicate(client):
    """测试重复记录检查"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "dup",
        "ip_address": "172.27.0.61",
    }

    first_response = client.post("/api/records", json=payload)
    assert first_response.status_code == 201

    duplicate_response = client.post("/api/records", json=payload)
    assert duplicate_response.status_code == 409
    assert "already exists" in duplicate_response.json()["detail"]


def test_update_record_success(client):
    """测试完整更新记录"""

    create_payload = {
        "zone": "seadee.com.cn",
        "hostname": "old",
        "ip_address": "172.27.0.70",
    }

    create_response = client.post("/api/records", json=create_payload)
    record_id = create_response.json()["data"]["id"]

    update_payload = {
        "zone": "seadee.com.cn",
        "hostname": "new",
        "ip_address": "172.27.0.71",
        "record_type": "A",
        "description": "Updated host",
        "status": "inactive",
    }

    response = client.put(f"/api/records/{record_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["hostname"] == "new"
    assert data["data"]["ip_address"] == "172.27.0.71"
    assert data["data"]["status"] == "inactive"


def test_patch_record_success(client):
    """测试部分更新记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "patch",
        "ip_address": "172.27.0.80",
    }
    create_response = client.post("/api/records", json=payload)
    record_id = create_response.json()["data"]["id"]

    patch_payload = {"ip_address": "172.27.0.81"}
    response = client.patch(f"/api/records/{record_id}", json=patch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["ip_address"] == "172.27.0.81"
    assert data["data"]["hostname"] == "patch"


def test_update_record_not_found(client):
    """测试更新不存在的记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "missing",
        "ip_address": "172.27.0.90",
        "record_type": "A",
        "status": "active",
    }

    response = client.put("/api/records/99999", json=payload)
    assert response.status_code == 404


def test_update_record_conflict(client):
    """测试更新冲突"""

    data1 = {"zone": "seadee.com.cn", "hostname": "conflict1", "ip_address": "10.0.0.1"}
    data2 = {"zone": "seadee.com.cn", "hostname": "conflict2", "ip_address": "10.0.0.2"}

    client.post("/api/records", json=data1)
    response2 = client.post("/api/records", json=data2)
    record2_id = response2.json()["data"]["id"]

    update_payload = {
        "zone": "seadee.com.cn",
        "hostname": "conflict1",
        "ip_address": "10.0.0.3",
        "record_type": "A",
        "status": "active",
    }

    response = client.put(f"/api/records/{record2_id}", json=update_payload)
    assert response.status_code == 409


def test_patch_record_validation(client):
    """测试 PATCH 验证逻辑"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "val",
        "ip_address": "172.27.0.100",
    }
    create_response = client.post("/api/records", json=payload)
    record_id = create_response.json()["data"]["id"]

    response = client.patch(
        f"/api/records/{record_id}", json={"ip_address": "invalid-ip"}
    )
    assert response.status_code == 422


def test_patch_record_deleted(client):
    """测试不能更新已删除的记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "todelete",
        "ip_address": "172.27.0.110",
    }
    create_response = client.post("/api/records", json=payload)
    record_id = create_response.json()["data"]["id"]

    delete_response = client.patch(
        f"/api/records/{record_id}", json={"status": "deleted"}
    )
    assert delete_response.status_code == 200

    response = client.patch(
        f"/api/records/{record_id}", json={"ip_address": "172.27.0.111"}
    )
    assert response.status_code == 400


def test_delete_record_soft(client):
    """测试软删除记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "softdelete",
        "ip_address": "172.27.0.120",
    }
    record_id = client.post("/api/records", json=payload).json()["data"]["id"]

    response = client.delete(f"/api/records/{record_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["mode"] == "soft"

    list_response = client.get("/api/records")
    assert record_id not in [r["id"] for r in list_response.json()["data"]]

    deleted_response = client.get("/api/records?include_deleted=true")
    assert record_id in [r["id"] for r in deleted_response.json()["data"]]
    for record in deleted_response.json()["data"]:
        if record["id"] == record_id:
            assert record["status"] == "deleted"


def test_delete_record_soft_twice(client):
    """测试重复软删除"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "softtwice",
        "ip_address": "172.27.0.121",
    }
    record_id = client.post("/api/records", json=payload).json()["data"]["id"]

    first = client.delete(f"/api/records/{record_id}")
    assert first.status_code == 200

    second = client.delete(f"/api/records/{record_id}")
    assert second.status_code == 400


def test_delete_record_hard(client):
    """测试硬删除记录"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "harddelete",
        "ip_address": "172.27.0.122",
    }
    record_id = client.post("/api/records", json=payload).json()["data"]["id"]

    response = client.delete(f"/api/records/{record_id}?mode=hard")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hard"

    not_found = client.delete(f"/api/records/{record_id}?mode=hard")
    assert not_found.status_code == 404


def test_delete_record_not_found(client):
    """测试删除不存在的记录"""

    response = client.delete("/api/records/99999")
    assert response.status_code == 404


def test_list_include_deleted_param(client):
    """测试 include_deleted 参数"""

    payload = {
        "zone": "seadee.com.cn",
        "hostname": "includedeleted",
        "ip_address": "172.27.0.123",
    }
    record_id = client.post("/api/records", json=payload).json()["data"]["id"]
    client.delete(f"/api/records/{record_id}")

    default_response = client.get("/api/records")
    assert record_id not in [r["id"] for r in default_response.json()["data"]]

    include_response = client.get("/api/records?include_deleted=true")
    assert record_id in [r["id"] for r in include_response.json()["data"]]


def test_search_records_full_text(client, sample_records):
    """测试全文搜索"""

    response = client.get("/api/records/search?q=app")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["hostname"] == "app"


def test_search_records_zone_filter(client, sample_records):
    """测试 Zone 过滤"""

    response = client.get("/api/records/search?zone=seadee.com.cn")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 2
    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"


def test_search_records_combined_filters(client, sample_records):
    """测试多条件组合"""

    response = client.get(
        "/api/records/search?zone=seadee.com.cn&status=active&record_type=A"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["zone"] == "seadee.com.cn"
    assert data["filters_applied"]["status"] == "active"
    assert data["filters_applied"]["record_type"] == "A"
    for record in data["data"]:
        assert record["zone"] == "seadee.com.cn"
        assert record["status"] == "active"


def test_search_records_date_range(client, session):
    """测试时间范围过滤"""

    old_record = DNSRecord(
        zone="legacy.com",
        hostname="old",
        ip_address="10.10.10.10",
        record_type="A",
        description="Old record",
        status="active",
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
        updated_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    session.add(old_record)
    new_record = DNSRecord(
        zone="legacy.com",
        hostname="new",
        ip_address="10.10.10.11",
        record_type="A",
        description="New record",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(new_record)
    session.commit()

    cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = client.get("/api/records/search", params={"created_after": cutoff})
    assert response.status_code == 200
    data = response.json()

    def normalize(dt: datetime) -> datetime:
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    cutoff_dt = normalize(datetime.fromisoformat(cutoff))
    assert all(
        normalize(datetime.fromisoformat(record["created_at"])) >= cutoff_dt
        for record in data["data"]
    )
    ids = [record["hostname"] for record in data["data"]]
    assert "new" in ids
    assert "old" not in ids


def test_search_records_no_results(client, sample_records):
    """测试空结果"""

    response = client.get("/api/records/search?q=thisrecorddoesnotexist")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 0
    assert len(data["data"]) == 0
