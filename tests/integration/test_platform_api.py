"""Integration tests for the sustainment API surface (ICD-PHM-002 rev C,
plus SYS-4412 readiness fields drafted for rev D)."""

import math

import pytest
from fastapi.testclient import TestClient

import src.main
from src.main import app
from src.models import Platform, Subsystem

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


# ── SYS-4412 · readiness fields (ICD-PHM-002 rev D draft) ─────────────────

REV_C_PLATFORM_FIELDS = {
    "platformId",
    "designation",
    "platformType",
    "operational",
    "subsystems",
}
REV_D_READINESS_FIELDS = {"readinessState", "readinessConfidence"}
EXPECTED_READINESS = {
    "LND-114": ("FMC", "HIGH"),
    "AIR-207": ("PMC", "HIGH"),
    "MSN-330": ("NMC", "LOW"),
}
LEAK_MARKERS = (
    "missionCriticalFault",
    "mission_critical_fault",
    "telemetryAgeSeconds",
    "telemetry_age_seconds",
    "PHM-RDY-1",
    "Traceback",
)


def test_list_endpoint_publishes_readiness_on_every_record():
    for record in client.get("/platforms").json():
        assert set(record) == REV_C_PLATFORM_FIELDS | REV_D_READINESS_FIELDS
        assert (record["readinessState"], record["readinessConfidence"]) == (
            EXPECTED_READINESS[record["platformId"]]
        )


@pytest.mark.parametrize("platform_id", ALL_PLATFORM_IDS)
def test_detail_endpoint_publishes_readiness(platform_id):
    record = client.get(f"/platforms/{platform_id}").json()

    assert set(record) == REV_C_PLATFORM_FIELDS | REV_D_READINESS_FIELDS
    assert (record["readinessState"], record["readinessConfidence"]) == (
        EXPECTED_READINESS[platform_id]
    )


def test_readiness_values_are_within_the_permitted_sets():
    for record in client.get("/platforms").json():
        assert record["readinessState"] in {"FMC", "PMC", "NMC"}
        assert record["readinessConfidence"] in {"HIGH", "LOW"}


def test_rev_c_fields_are_unchanged():
    record = client.get("/platforms/LND-114").json()

    assert {key: record[key] for key in REV_C_PLATFORM_FIELDS} == {
        "platformId": "LND-114",
        "designation": "Recovery Vehicle 114",
        "platformType": "LAND",
        "operational": True,
        "subsystems": [
            {
                "subsystemId": "PWR-01",
                "name": "Powerpack",
                "temperatureCelsius": 64.0,
                "operational": True,
            },
            {
                "subsystemId": "HYD-01",
                "name": "Hydraulic System",
                "temperatureCelsius": 51.0,
                "operational": True,
            },
        ],
    }


@pytest.mark.parametrize("path", ["/platforms", "/platforms/MSN-330"])
def test_readiness_payload_leaks_no_fault_age_or_rule_internals(path):
    body = client.get(path).text

    for marker in LEAK_MARKERS:
        assert marker not in body


@pytest.mark.parametrize(
    ("temperature", "state"),
    [(math.nan, "PMC"), (math.inf, "NMC"), (-math.inf, "PMC")],
    ids=["nan", "plus-inf", "minus-inf"],
)
def test_non_finite_temperature_serialises_and_is_classified(monkeypatch, temperature, state):
    platform = Platform(
        platform_id="TST-900",
        designation="Test Platform 900",
        platform_type="LAND",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="PWR-01",
                name="Powerpack",
                temperature_celsius=temperature,
                operational=True,
                mission_critical_fault=False,
                telemetry_age_seconds=0,
            )
        ],
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    detail = client.get("/platforms/TST-900")
    listed = client.get("/platforms")

    assert detail.status_code == 200
    assert listed.status_code == 200
    assert listed.json() == [detail.json()]
    record = detail.json()
    assert record["subsystems"][0]["temperatureCelsius"] is None
    assert (record["readinessState"], record["readinessConfidence"]) == (state, "LOW")


@pytest.mark.parametrize(
    "absent",
    ["telemetry_age_seconds", "mission_critical_fault", "operational"],
)
def test_absent_age_or_fault_flag_is_published_as_pmc_low(monkeypatch, absent):
    record = {
        "subsystem_id": "PWR-01",
        "name": "Powerpack",
        "temperature_celsius": 55.0,
        "operational": True,
        "mission_critical_fault": False,
        "telemetry_age_seconds": 0,
    }
    del record[absent]
    platform = Platform.model_validate(
        {
            "platform_id": "TST-901",
            "designation": "Test Platform 901",
            "platform_type": "LAND",
            "operational": True,
            "subsystems": [record],
        }
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    detail = client.get("/platforms/TST-901")
    listed = client.get("/platforms")

    assert detail.status_code == 200
    assert listed.json() == [detail.json()]
    body = detail.json()
    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "LOW")
    for marker in LEAK_MARKERS:
        assert marker not in detail.text


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        ("mission_critical_fault", 0),
        ("mission_critical_fault", "yes"),
        ("operational", 1),
        ("operational", "yes"),
    ],
    ids=["fault-int-0", "fault-str-yes", "operational-int-1", "operational-str-yes"],
)
def test_non_boolean_subsystem_flag_is_published_as_pmc_low(monkeypatch, flag, value):
    record = {
        "subsystem_id": "PWR-01",
        "name": "Powerpack",
        "temperature_celsius": 55.0,
        "operational": True,
        "mission_critical_fault": False,
        "telemetry_age_seconds": 0,
        flag: value,
    }
    platform = Platform.model_validate(
        {
            "platform_id": "TST-902",
            "designation": "Test Platform 902",
            "platform_type": "LAND",
            "operational": True,
            "subsystems": [record],
        }
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    detail = client.get("/platforms/TST-902")
    listed = client.get("/platforms")

    assert detail.status_code == 200
    assert listed.json() == [detail.json()]
    body = detail.json()
    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "LOW")
    assert body["subsystems"][0]["operational"] is (flag != "operational")
    for marker in LEAK_MARKERS:
        assert marker not in detail.text
