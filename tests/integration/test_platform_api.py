"""Integration tests for the sustainment API surface (ICD-PHM-002 rev C)."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

ALL_PLATFORM_IDS = ["LND-114", "AIR-207", "MSN-330"]


def test_list_endpoint_returns_every_platform():
    response = client.get("/platforms")

    assert response.status_code == 200
    assert [record["platformId"] for record in response.json()] == ALL_PLATFORM_IDS


@pytest.mark.parametrize("platform_id", ALL_PLATFORM_IDS)
def test_detail_endpoint_returns_requested_platform(platform_id):
    response = client.get(f"/platforms/{platform_id}")

    assert response.status_code == 200
    assert response.json()["platformId"] == platform_id


def test_detail_endpoint_returns_404_for_unknown_platform():
    response = client.get("/platforms/UNKNOWN-999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Platform not found"


def test_detail_error_does_not_leak_internal_diagnostics():
    body = client.get("/platforms/UNKNOWN-999").text

    assert "Traceback" not in body
    assert "src/" not in body


def test_list_and_detail_payloads_are_consistent():
    listed = {
        record["platformId"]: record for record in client.get("/platforms").json()
    }

    for platform_id in ALL_PLATFORM_IDS:
        assert client.get(f"/platforms/{platform_id}").json() == listed[platform_id]


def test_subsystem_payload_shape():
    subsystems = client.get("/platforms/MSN-330").json()["subsystems"]

    assert [s["subsystemId"] for s in subsystems] == ["GEN-01", "COM-01"]
    for subsystem in subsystems:
        assert set(subsystem.keys()) == {
            "subsystemId",
            "name",
            "temperatureCelsius",
            "operational",
        }


def test_openapi_document_is_served():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["version"] == "2.3.0"
    assert "/platforms" in document["paths"]
    assert "/platforms/{platform_id}" in document["paths"]
