"""Tests for CoreDNS reload/status endpoints"""

import pytest
from fastapi.testclient import TestClient

from app.main import application
from app.services.coredns_service import CoreDNSService


@pytest.fixture(scope="function")
def client():
    return TestClient(application)


def test_reload_success(client, monkeypatch):
    monkeypatch.setattr(CoreDNSService, "validate_corefile", lambda self, path: True)
    monkeypatch.setattr(
        CoreDNSService,
        "reload",
        lambda self: {"method": "process", "status": "success"},
    )

    response = client.post("/api/coredns/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "success"


def test_reload_invalid_corefile(client, monkeypatch):
    monkeypatch.setattr(CoreDNSService, "validate_corefile", lambda self, path: False)
    response = client.post("/api/coredns/reload")
    assert response.status_code == 400


def test_reload_failure(client, monkeypatch):
    monkeypatch.setattr(CoreDNSService, "validate_corefile", lambda self, path: True)

    def _raise(_self):
        raise RuntimeError("reload failed")

    monkeypatch.setattr(CoreDNSService, "reload", _raise)
    response = client.post("/api/coredns/reload")
    assert response.status_code == 500


def test_status_endpoint(client, monkeypatch):
    monkeypatch.setattr(
        CoreDNSService,
        "get_status",
        lambda self: {"method": "process", "running": True},
    )
    response = client.get("/api/coredns/status")
    assert response.status_code == 200
    assert response.json()["data"]["running"] is True
