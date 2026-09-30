"""Integration tests for the sustainment API surfaces: /platforms frozen at
ICD-PHM-002 rev C, and the SYS-4412 /v2 surface at ICD-PHM-002 rev D."""

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


# ── SYS-4412 · /v2 readiness surface (ICD-PHM-002 rev D) ─────────────────

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
    "SYS-4412-R1",
    "Traceback",
)


def test_list_endpoint_publishes_readiness_on_every_record():
    for record in client.get("/v2/platforms").json():
        assert set(record) == REV_C_PLATFORM_FIELDS | REV_D_READINESS_FIELDS
        assert (record["readinessState"], record["readinessConfidence"]) == (
            EXPECTED_READINESS[record["platformId"]]
        )


@pytest.mark.parametrize("platform_id", ALL_PLATFORM_IDS)
def test_detail_endpoint_publishes_readiness(platform_id):
    record = client.get(f"/v2/platforms/{platform_id}").json()

    assert set(record) == REV_C_PLATFORM_FIELDS | REV_D_READINESS_FIELDS
    assert (record["readinessState"], record["readinessConfidence"]) == (
        EXPECTED_READINESS[platform_id]
    )


def test_readiness_values_are_within_the_permitted_sets():
    for record in client.get("/v2/platforms").json():
        assert record["readinessState"] in {"FMC", "PMC", "NMC"}
        assert record["readinessConfidence"] in {"HIGH", "LOW"}


def test_rev_c_fields_are_unchanged():
    record = client.get("/v2/platforms/LND-114").json()

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


@pytest.mark.parametrize("path", ["/v2/platforms", "/v2/platforms/MSN-330"])
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

    detail = client.get("/v2/platforms/TST-900")
    listed = client.get("/v2/platforms")

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

    detail = client.get("/v2/platforms/TST-901")
    listed = client.get("/v2/platforms")

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

    detail = client.get("/v2/platforms/TST-902")
    listed = client.get("/v2/platforms")

    assert detail.status_code == 200
    assert listed.json() == [detail.json()]
    body = detail.json()
    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "LOW")
    assert body["subsystems"][0]["operational"] is (flag != "operational")
    for marker in LEAK_MARKERS:
        assert marker not in detail.text


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("temperature_celsius", True),
        ("temperature_celsius", "95"),
        ("temperature_celsius", "inf"),
        ("telemetry_age_seconds", False),
        ("telemetry_age_seconds", "10"),
    ],
    ids=["temp-bool", "temp-str-95", "temp-str-inf", "age-bool", "age-str-10"],
)
def test_malformed_temperature_or_age_is_published_as_pmc_low(monkeypatch, field, value):
    record = {
        "subsystem_id": "PWR-01",
        "name": "Powerpack",
        "temperature_celsius": 55.0,
        "operational": True,
        "mission_critical_fault": False,
        "telemetry_age_seconds": 0,
        field: value,
    }
    platform = Platform.model_validate(
        {
            "platform_id": "TST-903",
            "designation": "Test Platform 903",
            "platform_type": "LAND",
            "operational": True,
            "subsystems": [record],
        }
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    detail = client.get("/v2/platforms/TST-903")
    listed = client.get("/v2/platforms")

    assert detail.status_code == 200
    assert listed.json() == [detail.json()]
    body = detail.json()
    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "LOW")
    expected_temperature = None if field == "temperature_celsius" else 55.0
    assert body["subsystems"][0]["temperatureCelsius"] == expected_temperature
    for marker in LEAK_MARKERS:
        assert marker not in detail.text


@pytest.mark.parametrize(
    "age", [10**400, -(10**400)], ids=["int-10**400", "int-minus-10**400"]
)
def test_oversized_int_age_is_published_as_pmc_low(monkeypatch, age):
    # SYS-4412: an integer age too large to compare safely is malformed
    # telemetry, never a server error.
    platform = Platform.model_validate(
        {
            "platform_id": "TST-904",
            "designation": "Test Platform 904",
            "platform_type": "LAND",
            "operational": True,
            "subsystems": [
                {
                    "subsystem_id": "PWR-01",
                    "name": "Powerpack",
                    "temperature_celsius": 55.0,
                    "operational": True,
                    "mission_critical_fault": False,
                    "telemetry_age_seconds": age,
                }
            ],
        }
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    detail = client.get("/v2/platforms/TST-904")
    listed = client.get("/v2/platforms")

    assert detail.status_code == 200
    assert listed.status_code == 200
    assert listed.json() == [detail.json()]
    body = detail.json()
    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "LOW")
    assert body["subsystems"][0]["temperatureCelsius"] == 55.0
    for marker in LEAK_MARKERS:
        assert marker not in detail.text
        assert marker not in listed.text


# ── SYS-4412 · /v2 surface shape and separation from rev C ────────────────


def test_rev_c_paths_publish_no_readiness_fields():
    listed = client.get("/platforms").json()
    detail = [client.get(f"/platforms/{pid}").json() for pid in ALL_PLATFORM_IDS]

    for record in listed + detail:
        assert set(record) == REV_C_PLATFORM_FIELDS


def test_v2_rev_c_fields_match_the_rev_c_surface():
    rev_c = {r["platformId"]: r for r in client.get("/platforms").json()}

    for record in client.get("/v2/platforms").json():
        assert {key: record[key] for key in REV_C_PLATFORM_FIELDS} == rev_c[
            record["platformId"]
        ]


def test_v2_list_returns_every_platform_in_order():
    response = client.get("/v2/platforms")

    assert response.status_code == 200
    assert [record["platformId"] for record in response.json()] == ALL_PLATFORM_IDS


def test_v2_list_and_detail_payloads_are_consistent():
    listed = {r["platformId"]: r for r in client.get("/v2/platforms").json()}

    for platform_id in ALL_PLATFORM_IDS:
        assert client.get(f"/v2/platforms/{platform_id}").json() == listed[platform_id]


def test_v2_detail_returns_404_without_diagnostics():
    response = client.get("/v2/platforms/UNKNOWN-999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Platform not found"}
    assert "Traceback" not in response.text


def test_v2_openapi_document_is_rev_d_at_2_4_0():
    response = client.get("/v2/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["version"] == "2.4.0"
    assert set(document["paths"]) == {"/platforms", "/platforms/{platform_id}"}


def test_root_openapi_document_stays_rev_c_at_2_3_0():
    document = client.get("/openapi.json").json()

    assert document["info"]["version"] == "2.3.0"
    assert set(document["paths"]) == {"/platforms", "/platforms/{platform_id}"}
    assert "readinessState" not in client.get("/openapi.json").text


@pytest.mark.parametrize(
    ("age", "expected"),
    [(300, ("FMC", "HIGH")), (301, ("PMC", "LOW"))],
    ids=["300s-fresh", "301s-stale"],
)
def test_v2_staleness_boundary(monkeypatch, age, expected):
    platform = Platform(
        platform_id="TST-905",
        designation="Test Platform 905",
        platform_type="LAND",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="PWR-01",
                name="Powerpack",
                temperature_celsius=55.0,
                operational=True,
                mission_critical_fault=False,
                telemetry_age_seconds=age,
            )
        ],
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)

    body = client.get("/v2/platforms/TST-905").json()

    assert (body["readinessState"], body["readinessConfidence"]) == expected
    assert set(client.get("/platforms/TST-905").json()) == REV_C_PLATFORM_FIELDS


@pytest.mark.parametrize(
    ("temperature", "expected"),
    [
        (69.9, "FMC"),
        (70.0, "PMC"),
        (89.9, "PMC"),
        (90.0, "NMC"),
    ],
)
def test_v2_temperature_boundaries(monkeypatch, temperature, expected):
    platform = Platform(
        platform_id="TST-906",
        designation="Test Platform 906",
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
    monkeypatch.setattr(src.main, "list_platforms", lambda: [platform])

    (body,) = client.get("/v2/platforms").json()

    assert (body["readinessState"], body["readinessConfidence"]) == (expected, "HIGH")


def test_v2_degraded_subsystem_is_pmc(monkeypatch):
    platform = Platform(
        platform_id="TST-907",
        designation="Test Platform 907",
        platform_type="LAND",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="PWR-01",
                name="Powerpack",
                temperature_celsius=55.0,
                operational=False,
                mission_critical_fault=False,
                telemetry_age_seconds=0,
            )
        ],
    )
    monkeypatch.setattr(src.main, "get_platform", lambda _id: platform)

    body = client.get("/v2/platforms/TST-907").json()

    assert (body["readinessState"], body["readinessConfidence"]) == ("PMC", "HIGH")
    assert body["subsystems"][0]["operational"] is False


def _rev_c_subsystem(subsystem_id, name, temperature):
    return {
        "subsystemId": subsystem_id,
        "name": name,
        "temperatureCelsius": temperature,
        "operational": True,
    }


def test_rev_c_list_payload_is_unchanged_from_phms_2_3_0():
    assert client.get("/platforms").json() == [
        {
            "platformId": "LND-114",
            "designation": "Recovery Vehicle 114",
            "platformType": "LAND",
            "operational": True,
            "subsystems": [
                _rev_c_subsystem("PWR-01", "Powerpack", 64.0),
                _rev_c_subsystem("HYD-01", "Hydraulic System", 51.0),
            ],
        },
        {
            "platformId": "AIR-207",
            "designation": "Rotary Platform 207",
            "platformType": "AIR",
            "operational": True,
            "subsystems": [
                _rev_c_subsystem("GBX-01", "Main Gearbox", 78.0),
                _rev_c_subsystem("AVN-01", "Mission Avionics", 42.0),
            ],
        },
        {
            "platformId": "MSN-330",
            "designation": "Deployable Mission System 330",
            "platformType": "MISSION_SYSTEM",
            "operational": True,
            "subsystems": [
                _rev_c_subsystem("GEN-01", "Prime Power Generator", 94.0),
                _rev_c_subsystem("COM-01", "Comms Suite", 55.0),
            ],
        },
    ]
