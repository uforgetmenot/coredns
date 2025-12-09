"""Test Corefile generation with upstream DNS"""

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.config import settings
from app.models.dns_record import DNSRecord
from app.models.setting import SystemSetting
from app.services.corefile_service import CorefileService
from app.services.settings_service import SettingsService


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    DNSRecord.metadata.create_all(engine)
    SystemSetting.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_corefile_generation_with_custom_dns(session: Session):
    """Test Corefile generation with custom upstream DNS"""
    # Set custom upstream DNS
    settings_service = SettingsService(session)
    settings_service.set_upstream_dns("1.1.1.1", "1.0.0.1")

    # Add a test DNS record
    record = DNSRecord(
        hostname="test",
        zone="example.com",
        ip_address="192.168.1.100",
        status="active",
    )
    session.add(record)
    session.commit()

    # Generate Corefile
    corefile_service = CorefileService()
    result = corefile_service.generate_corefile(session=session)

    # Verify the content contains custom DNS servers
    assert "forward . 1.1.1.1 1.0.0.1" in result["content"]
    assert "test.example.com" in result["content"]


def test_corefile_generation_with_primary_dns_only(session: Session):
    """Test Corefile generation with only primary DNS"""
    # Set only primary DNS
    settings_service = SettingsService(session)
    settings_service.set_upstream_dns("1.1.1.1", None)

    # Generate Corefile
    corefile_service = CorefileService()
    result = corefile_service.generate_corefile(session=session)

    # Verify the content contains only primary DNS and not a second one
    content = result["content"]
    assert "forward . 1.1.1.1" in content
    # Make sure we don't have two IP addresses on the forward line
    # by checking that there's no pattern like "1.1.1.1 X.X.X.X"
    import re
    # Match "forward . IP IP" pattern
    pattern = r'forward\s+\.\s+\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+'
    assert not re.search(pattern, content), "Should not have two IP addresses in forward directive"


def test_corefile_generation_with_default_dns(session: Session):
    """Test Corefile generation with default DNS"""
    # Initialize default settings
    settings_service = SettingsService(session)
    settings_service.initialize_default_settings()

    # Generate Corefile
    corefile_service = CorefileService()
    result = corefile_service.generate_corefile(session=session)

    # Verify the content contains default DNS servers
    parts = [settings.upstream_primary_dns_default]
    if settings.upstream_secondary_dns_default:
        parts.append(settings.upstream_secondary_dns_default)
    forward_line = "forward . " + " ".join(parts)
    assert forward_line in result["content"]
