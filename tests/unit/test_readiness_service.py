"""Unit tests for the platform summary projection (SYS-4400)."""

from src.models import Platform, Subsystem
from src.readiness_service import get_platform_summary
from src.repository import PLATFORMS, get_platform, list_platforms

SUBSYSTEM_FIELDS = {"subsystemId", "name", "temperatureCelsius", "operational"}


def _platform(**overrides) -> Platform:
    defaults = dict(
        platform_id="TST-001",
        designation="Test Platform 001",
        platform_type="LAND",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="PWR-01",
                name="Powerpack",
                temperature_celsius=55.0,
            )
        ],
    )
    defaults.update(overrides)
    return Platform(**defaults)


def test_summary_maps_platform_fields_to_icd_names():
    summary = get_platform_summary(_platform())

    assert summary["platformId"] == "TST-001"
    assert summary["designation"] == "Test Platform 001"
    assert summary["platformType"] == "LAND"
    assert summary["operational"] is True


def test_summary_maps_subsystem_fields_to_icd_names():
    summary = get_platform_summary(_platform())

    subsystem = summary["subsystems"][0]
    assert set(subsystem.keys()) == SUBSYSTEM_FIELDS
    assert subsystem["subsystemId"] == "PWR-01"
    assert subsystem["name"] == "Powerpack"
    assert subsystem["temperatureCelsius"] == 55.0
    assert subsystem["operational"] is True


def test_summary_never_exposes_internal_diagnostics():
    platform = _platform(
        subsystems=[
            Subsystem(
                subsystem_id="GEN-01",
                name="Prime Power Generator",
                temperature_celsius=94.0,
                mission_critical_fault=True,
                telemetry_age_seconds=3600,
            )
        ]
    )

    subsystem = get_platform_summary(platform)["subsystems"][0]

    assert "missionCriticalFault" not in subsystem
    assert "telemetryAgeSeconds" not in subsystem
    assert "mission_critical_fault" not in subsystem
    assert "telemetry_age_seconds" not in subsystem


def test_summary_preserves_subsystem_order_and_count():
    platform = _platform(
        subsystems=[
            Subsystem(subsystem_id="A-01", name="Alpha"),
            Subsystem(subsystem_id="B-01", name="Bravo"),
            Subsystem(subsystem_id="C-01", name="Charlie"),
        ]
    )

    summary = get_platform_summary(platform)

    assert [s["subsystemId"] for s in summary["subsystems"]] == [
        "A-01",
        "B-01",
        "C-01",
    ]


def test_summary_passes_through_absent_temperature_as_null():
    platform = _platform(
        subsystems=[Subsystem(subsystem_id="COM-01", name="Comms Suite")]
    )

    assert get_platform_summary(platform)["subsystems"][0][
        "temperatureCelsius"
    ] is None


def test_summary_reflects_non_operational_platform():
    summary = get_platform_summary(_platform(operational=False))

    assert summary["operational"] is False


def test_get_platform_returns_known_platform():
    platform = get_platform("AIR-207")

    assert platform is not None
    assert platform.designation == "Rotary Platform 207"


def test_get_platform_returns_none_for_unknown_platform():
    assert get_platform("NOPE-000") is None


def test_list_platforms_covers_all_three_domains():
    platform_types = {platform.platform_type for platform in list_platforms()}

    assert platform_types == {"LAND", "AIR", "MISSION_SYSTEM"}
    assert len(list_platforms()) == len(PLATFORMS)
