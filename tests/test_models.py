"""
测试数据库模型
"""

import pytest
import os
import tempfile
from sqlmodel import Session, select, create_engine
from sqlmodel import SQLModel
from app.models import DNSRecord, Zone, CorefileBackup, OperationLog, SystemSetting


@pytest.fixture(scope="function")
def session():
    """创建独立的测试数据库会话"""
    # 创建临时数据库文件
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    database_url = f"sqlite:///{temp_db.name}"

    # 创建引擎和表
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    # 创建会话
    with Session(engine) as session:
        yield session

    # 清理
    engine.dispose()
    os.unlink(temp_db.name)


def test_create_dns_record(session):
    """测试创建 DNS 记录"""
    record = DNSRecord(
        zone="test.com",
        hostname="www",
        ip_address="192.168.1.1",
        record_type="A",
        description="Test record",
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    assert record.id is not None
    assert record.zone == "test.com"
    assert record.hostname == "www"
    assert record.status == "active"
    assert record.created_at is not None


def test_create_zone(session):
    """测试创建 Zone"""
    zone = Zone(
        name="example.com",
        fallthrough=True,
        log_enabled=True,
        upstream_dns="8.8.8.8",
    )
    session.add(zone)
    session.commit()
    session.refresh(zone)

    assert zone.id is not None
    assert zone.name == "example.com"
    assert zone.status == "active"
    assert zone.created_at is not None


def test_zone_unique_constraint(session):
    """测试 Zone 名称唯一性约束"""
    zone1 = Zone(name="unique.com")
    session.add(zone1)
    session.commit()

    # 尝试创建同名 Zone
    zone2 = Zone(name="unique.com")
    session.add(zone2)

    with pytest.raises(Exception):  # SQLite IntegrityError
        session.commit()


def test_create_corefile_backup(session):
    """测试创建 Corefile 备份"""
    backup = CorefileBackup(
        content=". {\\n  forward . 8.8.8.8\\n}",
        backup_reason="Before update",
    )
    session.add(backup)
    session.commit()
    session.refresh(backup)

    assert backup.id is not None
    assert "forward" in backup.content
    assert backup.created_at is not None


def test_create_operation_log(session):
    """测试创建操作日志"""
    log = OperationLog(
        operation_type="create",
        resource_type="record",
        resource_id=1,
        details='{"zone": "test.com"}',
        user="admin",
        ip_address="127.0.0.1",
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    assert log.id is not None
    assert log.operation_type == "create"
    assert log.user == "admin"
    assert log.created_at is not None


def test_create_system_setting(session):
    """测试创建系统设置"""
    setting = SystemSetting(
        key="log_retention_days",
        value="30",
        description="日志保留天数",
    )
    session.add(setting)
    session.commit()
    session.refresh(setting)

    assert setting.id is not None
    assert setting.key == "log_retention_days"
    assert setting.value == "30"
    assert setting.updated_at is not None


def test_query_dns_records(session):
    """测试查询 DNS 记录"""
    # 创建测试数据
    records = [
        DNSRecord(zone="test.com", hostname="www", ip_address="192.168.1.1"),
        DNSRecord(zone="test.com", hostname="api", ip_address="192.168.1.2"),
        DNSRecord(zone="example.com", hostname="www", ip_address="10.0.0.1"),
    ]
    for record in records:
        session.add(record)
    session.commit()

    # 查询所有记录
    all_records = session.exec(select(DNSRecord)).all()
    assert len(all_records) >= 3

    # 按 zone 过滤
    test_com_records = session.exec(
        select(DNSRecord).where(DNSRecord.zone == "test.com")
    ).all()
    assert len(test_com_records) >= 2
