"""Tests for upstream DNS settings"""

import pytest
from sqlmodel import Session, create_engine
from sqlmodel.pool import StaticPool

from app.config import settings
from app.models.setting import SystemSetting
from app.services.settings_service import SettingsService


@pytest.fixture(name="session")
def session_fixture():
    """Create a test database session"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SystemSetting.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_get_default_upstream_dns(session: Session):
    """Test getting default upstream DNS values"""
    service = SettingsService(session)

    # Initialize default settings first
    service.initialize_default_settings()

    primary, secondary = service.get_upstream_dns()
    assert primary == settings.upstream_primary_dns_default
    assert secondary == settings.upstream_secondary_dns_default


def test_set_upstream_dns(session: Session):
    """Test setting upstream DNS values"""
    service = SettingsService(session)

    # Set new DNS values
    primary, secondary = service.set_upstream_dns("1.1.1.1", "1.0.0.1")
    assert primary == "1.1.1.1"
    assert secondary == "1.0.0.1"

    # Verify they were persisted
    primary, secondary = service.get_upstream_dns()
    assert primary == "1.1.1.1"
    assert secondary == "1.0.0.1"


def test_set_upstream_dns_primary_only(session: Session):
    """Test setting only primary DNS"""
    service = SettingsService(session)

    # Set primary DNS only
    primary, secondary = service.set_upstream_dns("1.1.1.1", None)
    assert primary == "1.1.1.1"
    assert secondary is None

    # Verify
    primary, secondary = service.get_upstream_dns()
    assert primary == "1.1.1.1"
    assert secondary is None


def test_update_upstream_dns(session: Session):
    """Test updating existing upstream DNS values"""
    service = SettingsService(session)

    # Set initial values
    service.set_upstream_dns(
        settings.upstream_primary_dns_default,
        settings.upstream_secondary_dns_default,
    )

    # Update to new values
    primary, secondary = service.set_upstream_dns("1.1.1.1", "1.0.0.1")
    assert primary == "1.1.1.1"
    assert secondary == "1.0.0.1"


def test_initialize_default_settings(session: Session):
    """Test initializing default settings"""
    service = SettingsService(session)
    service.initialize_default_settings()

    primary, secondary = service.get_upstream_dns()
    assert primary == settings.upstream_primary_dns_default
    assert secondary == settings.upstream_secondary_dns_default
