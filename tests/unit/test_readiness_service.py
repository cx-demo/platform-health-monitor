"""Unit tests for the platform summary projection (SYS-4400) and the
PHM-RDY-1 readiness classifier (SYS-4412)."""

import math

import pytest

from src.models import (
    Platform,
    ReadinessConfidence,
    ReadinessState,
    Subsystem,
)
from src.readiness_service import (
    READINESS_RULE_VERSION,
    STALE_TELEMETRY_AGE_SECONDS,
    classify_readiness,
    get_platform_summary,
)
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
                operational=True,
                mission_critical_fault=False,
                telemetry_age_seconds=0,
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


# ── SYS-4412 · PHM-RDY-1 readiness classifier ─────────────────────────────

FMC, PMC, NMC = ReadinessState.FMC, ReadinessState.PMC, ReadinessState.NMC
HIGH, LOW = ReadinessConfidence.HIGH, ReadinessConfidence.LOW


def _sub(subsystem_id="S-01", **overrides) -> Subsystem:
    """Fresh, fault-free, explicitly reported telemetry unless overridden."""
    fields = dict(
        subsystem_id=subsystem_id,
        name="Subsystem",
        temperature_celsius=50.0,
        operational=True,
        mission_critical_fault=False,
        telemetry_age_seconds=0,
    )
    fields.update(overrides)
    return Subsystem(**fields)


def _malformed_sub(**overrides) -> Subsystem:
    """Bypass model validation to simulate a malformed upstream record."""
    fields = dict(
        subsystem_id="BAD-01",
        name="Malformed",
        temperature_celsius=50.0,
        operational=True,
        mission_critical_fault=False,
        telemetry_age_seconds=0,
    )
    fields.update(overrides)
    return Subsystem.model_construct(**fields)


def _classify(*subsystems, operational=True):
    return classify_readiness(
        _platform(operational=operational, subsystems=list(subsystems))
    )


def test_rule_version_is_phm_rdy_1():
    assert READINESS_RULE_VERSION == "PHM-RDY-1"


def test_permitted_readiness_values_are_exactly_fmc_pmc_nmc():
    assert {state.value for state in ReadinessState} == {"FMC", "PMC", "NMC"}
    assert {c.value for c in ReadinessConfidence} == {"HIGH", "LOW"}


def test_rule_7_all_nominal_is_fmc_high():
    result = _classify(_sub("A"), _sub("B", temperature_celsius=20.0))

    assert (result.state, result.confidence) == (FMC, HIGH)


def test_rule_1_mission_critical_fault_is_nmc():
    result = _classify(_sub("A"), _sub("B", mission_critical_fault=True))

    assert (result.state, result.confidence) == (NMC, HIGH)


def test_rule_1_fault_overrides_otherwise_nominal_readings():
    result = _classify(_sub(temperature_celsius=20.0, mission_critical_fault=True))

    assert result.state is NMC


def test_rule_3_platform_not_operational_is_nmc():
    result = _classify(_sub(), operational=False)

    assert (result.state, result.confidence) == (NMC, HIGH)


def test_rule_3_subsystem_not_operational_without_fault_is_nmc():
    result = _classify(_sub("A"), _sub("B", operational=False))

    assert (result.state, result.confidence) == (NMC, HIGH)


def test_rule_3_takes_precedence_over_rule_4():
    result = _classify(_sub(temperature_celsius=75.0), operational=False)

    assert result.state is NMC


@pytest.mark.parametrize(
    ("temperature", "expected"),
    [
        (69.9, FMC),
        (70.0, PMC),
        (89.9, PMC),
        (90.0, NMC),
    ],
)
def test_temperature_boundaries(temperature, expected):
    result = _classify(_sub(temperature_celsius=temperature))

    assert result.state is expected
    assert result.confidence is HIGH


def test_rule_2_hottest_subsystem_governs():
    result = _classify(_sub("A", temperature_celsius=75.0), _sub("B", temperature_celsius=95.0))

    assert result.state is NMC


def test_rule_4_one_warm_subsystem_is_pmc():
    result = _classify(_sub("A", temperature_celsius=20.0), _sub("B", temperature_celsius=70.0))

    assert (result.state, result.confidence) == (PMC, HIGH)


def test_rule_5_is_reserved_and_never_matches_on_nominal_data():
    assert _classify(_sub()).state is FMC


@pytest.mark.parametrize(
    "temperature",
    [None, math.nan, -math.inf],
    ids=["missing", "nan", "minus-inf"],
)
def test_rule_6_missing_nan_or_minus_inf_temperature_is_pmc_low(temperature):
    result = _classify(_sub("A"), _sub("B", temperature_celsius=temperature))

    assert (result.state, result.confidence) == (PMC, LOW)


@pytest.mark.parametrize("temperature", [math.inf], ids=["float-inf"])
def test_rule_2_plus_inf_temperature_is_nmc_low(temperature):
    subsystem = Subsystem.model_validate(
        {
            "subsystem_id": "B",
            "name": "Subsystem",
            "temperature_celsius": temperature,
            "operational": True,
            "mission_critical_fault": False,
            "telemetry_age_seconds": 0,
        }
    )

    result = _classify(_sub("A"), subsystem)

    assert subsystem.temperature_celsius == math.inf
    assert (result.state, result.confidence) == (NMC, LOW)


def test_rule_2_plus_inf_takes_precedence_over_rule_3_and_4():
    result = _classify(
        _sub("A", temperature_celsius=75.0),
        _sub("B", temperature_celsius=math.inf),
        operational=False,
    )

    assert (result.state, result.confidence) == (NMC, LOW)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (0, (FMC, HIGH)),
        (STALE_TELEMETRY_AGE_SECONDS - 1, (FMC, HIGH)),
        (STALE_TELEMETRY_AGE_SECONDS, (PMC, LOW)),
        (STALE_TELEMETRY_AGE_SECONDS + 1, (PMC, LOW)),
        (3600, (PMC, LOW)),
    ],
)
def test_rule_6_staleness_boundary_at_300_seconds(age, expected):
    result = _classify(_sub(telemetry_age_seconds=age))

    assert STALE_TELEMETRY_AGE_SECONDS == 300
    assert (result.state, result.confidence) == expected


@pytest.mark.parametrize(
    "overrides",
    [
        {"temperature_celsius": "hot"},
        {"temperature_celsius": True},
        {"telemetry_age_seconds": "recent"},
        {"telemetry_age_seconds": None},
        {"telemetry_age_seconds": -1},
        {"telemetry_age_seconds": math.nan},
    ],
    ids=[
        "temperature-string",
        "temperature-bool",
        "age-string",
        "age-none",
        "age-negative",
        "age-nan",
    ],
)
def test_rule_6_malformed_telemetry_is_pmc_low(overrides):
    result = _classify(_sub("A"), _malformed_sub(**overrides))

    assert (result.state, result.confidence) == (PMC, LOW)


# Malformed temperature and age, through normal model validation.

_VALID_SUBSYSTEM = {
    "subsystem_id": "S-01",
    "name": "Subsystem",
    "temperature_celsius": 50.0,
    "operational": True,
    "mission_critical_fault": False,
    "telemetry_age_seconds": 0,
}

_MALFORMED_TEMPERATURES = [
    True, False, "85.0", "95", "50", "inf", "Infinity", "nan", "", "hot", [], {},
]
_MALFORMED_TEMPERATURE_IDS = [
    "bool-true", "bool-false", "str-85.0", "str-95", "str-50", "str-inf",
    "str-infinity", "str-nan", "empty-str", "str-hot", "list", "dict",
]
_MALFORMED_AGES = [
    True, False, "10", "0", "10.0", "", "recent", 10.5, math.nan,
    math.inf, -math.inf, [], {},
]
_MALFORMED_AGE_IDS = [
    "bool-true", "bool-false", "str-10", "str-0", "str-10.0", "empty-str",
    "str-recent", "float-10.5", "float-nan", "float-inf", "float-minus-inf",
    "list", "dict",
]


@pytest.mark.parametrize(
    "value", _MALFORMED_TEMPERATURES, ids=_MALFORMED_TEMPERATURE_IDS
)
def test_malformed_temperature_is_not_coerced_by_validation(value):
    subsystem = Subsystem.model_validate(
        {**_VALID_SUBSYSTEM, "temperature_celsius": value}
    )
    result = _classify(_sub("A"), subsystem)

    assert subsystem.temperature_celsius is None
    assert result.state is not FMC
    assert (result.state, result.confidence) == (PMC, LOW)


@pytest.mark.parametrize("value", _MALFORMED_AGES, ids=_MALFORMED_AGE_IDS)
def test_malformed_age_is_not_coerced_by_validation(value):
    subsystem = Subsystem.model_validate(
        {**_VALID_SUBSYSTEM, "telemetry_age_seconds": value}
    )
    result = _classify(_sub("A"), subsystem)

    assert subsystem.telemetry_age_seconds is None
    assert result.state is not FMC
    assert (result.state, result.confidence) == (PMC, LOW)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("temperature_celsius", True),
        ("temperature_celsius", "85.0"),
        ("telemetry_age_seconds", True),
        ("telemetry_age_seconds", "10"),
    ],
    ids=["temperature-bool", "temperature-str", "age-bool", "age-str"],
)
def test_malformed_temperature_or_age_via_platform_validation_is_pmc_low(
    field, value
):
    platform = Platform.model_validate(
        {
            "platform_id": "TST-003",
            "designation": "Test Platform 003",
            "platform_type": "LAND",
            "operational": True,
            "subsystems": [{**_VALID_SUBSYSTEM, field: value}],
        }
    )

    result = classify_readiness(platform)
    summary = get_platform_summary(platform)

    assert getattr(platform.subsystems[0], field) is None
    assert (result.state, result.confidence) == (PMC, LOW)
    assert (summary["readinessState"], summary["readinessConfidence"]) == (
        "PMC",
        "LOW",
    )


def test_malformed_temperature_with_real_fault_elsewhere_is_nmc_low():
    malformed = Subsystem.model_validate(
        {**_VALID_SUBSYSTEM, "temperature_celsius": "95"}
    )

    result = _classify(_sub("A", mission_critical_fault=True), malformed)

    assert (result.state, result.confidence) == (NMC, LOW)


@pytest.mark.parametrize(
    ("temperature", "age"),
    [
        (50.0, 10),
        (50, 10),
        (50.0, 0),
        (50.0, 10.0),
        (69.9, STALE_TELEMETRY_AGE_SECONDS - 1),
    ],
    ids=[
        "float-50.0-int-10",
        "int-50-int-10",
        "float-50.0-int-0",
        "float-50.0-whole-float-10.0",
        "boundary",
    ],
)
def test_real_number_temperature_and_age_are_valid(temperature, age):
    subsystem = Subsystem.model_validate(
        {
            **_VALID_SUBSYSTEM,
            "temperature_celsius": temperature,
            "telemetry_age_seconds": age,
        }
    )
    result = _classify(subsystem)

    assert subsystem.temperature_celsius == float(temperature)
    assert isinstance(subsystem.temperature_celsius, float)
    assert subsystem.telemetry_age_seconds == age
    assert type(subsystem.telemetry_age_seconds) is int
    assert (result.state, result.confidence) == (FMC, HIGH)


def test_whole_float_stale_age_is_still_stale():
    subsystem = Subsystem.model_validate(
        {**_VALID_SUBSYSTEM, "telemetry_age_seconds": 300.0}
    )

    assert subsystem.telemetry_age_seconds == STALE_TELEMETRY_AGE_SECONDS
    assert (_classify(subsystem).state, _classify(subsystem).confidence) == (
        PMC,
        LOW,
    )


def test_rule_6_no_subsystems_is_pmc_low():
    result = _classify()

    assert (result.state, result.confidence) == (PMC, LOW)


# Absence is tested through normal model validation (no model_construct).

_REPORTED_SUBSYSTEM = {
    "subsystem_id": "S-01",
    "name": "Subsystem",
    "temperature_celsius": 50.0,
    "operational": True,
}


@pytest.mark.parametrize(
    "absent",
    [
        ("telemetry_age_seconds",),
        ("mission_critical_fault",),
        ("telemetry_age_seconds", "mission_critical_fault"),
    ],
    ids=["age-absent", "fault-flag-absent", "both-absent"],
)
def test_rule_6_absent_age_or_fault_flag_is_missing_telemetry(absent):
    record = {
        **_REPORTED_SUBSYSTEM,
        "mission_critical_fault": False,
        "telemetry_age_seconds": 0,
    }
    for key in absent:
        del record[key]

    subsystem = Subsystem.model_validate(record)
    result = _classify(_sub("A"), subsystem)

    for key in absent:
        assert getattr(subsystem, key) is None
    assert (result.state, result.confidence) == (PMC, LOW)


def test_subsystem_absent_age_and_fault_flag_default_to_none_not_fresh_or_false():
    subsystem = Subsystem(subsystem_id="S-01", name="Subsystem", temperature_celsius=50.0)

    assert subsystem.telemetry_age_seconds is None
    assert subsystem.mission_critical_fault is None
    assert _classify(subsystem).state is not FMC


@pytest.mark.parametrize(
    "explicit_none",
    ["telemetry_age_seconds", "mission_critical_fault"],
)
def test_rule_6_explicit_null_age_or_fault_flag_validates_as_missing(explicit_none):
    record = {
        **_REPORTED_SUBSYSTEM,
        "mission_critical_fault": False,
        "telemetry_age_seconds": 0,
        explicit_none: None,
    }

    result = _classify(Subsystem.model_validate(record))

    assert (result.state, result.confidence) == (PMC, LOW)


def test_absent_fault_flag_with_high_temperature_is_nmc_low():
    subsystem = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "temperature_celsius": 90.0, "telemetry_age_seconds": 0}
    )

    result = _classify(subsystem)

    assert (result.state, result.confidence) == (NMC, LOW)


def test_absent_age_with_reported_fault_is_nmc_low():
    subsystem = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "mission_critical_fault": True}
    )

    result = _classify(subsystem)

    assert (result.state, result.confidence) == (NMC, LOW)


@pytest.mark.parametrize(
    "fault_flag",
    ["yes", 1, 0],
    ids=["fault-string", "fault-int-1", "fault-int-0"],
)
def test_rule_6_malformed_fault_flag_is_bad_telemetry_and_never_fmc(fault_flag):
    result = _classify(_malformed_sub(mission_critical_fault=fault_flag))

    assert result.confidence is LOW
    assert result.state is not FMC


def test_fleet_fixtures_report_age_and_fault_flag_explicitly():
    for platform in list_platforms():
        for subsystem in platform.subsystems:
            assert "telemetry_age_seconds" in subsystem.model_fields_set
            assert "mission_critical_fault" in subsystem.model_fields_set


def test_fleet_fixtures_report_subsystem_operational_flag_explicitly():
    for platform in list_platforms():
        for subsystem in platform.subsystems:
            assert "operational" in subsystem.model_fields_set
            assert isinstance(subsystem.operational, bool)


# Absent or malformed operational/fault flags, through normal validation.


def test_absent_subsystem_operational_flag_is_missing_telemetry():
    record = {**_REPORTED_SUBSYSTEM, "mission_critical_fault": False, "telemetry_age_seconds": 0}
    del record["operational"]

    subsystem = Subsystem.model_validate(record)
    result = _classify(_sub("A"), subsystem)

    assert subsystem.operational is None
    assert (result.state, result.confidence) == (PMC, LOW)


def test_subsystem_operational_flag_defaults_to_none_not_true():
    subsystem = Subsystem(
        subsystem_id="S-01",
        name="Subsystem",
        temperature_celsius=50.0,
        mission_critical_fault=False,
        telemetry_age_seconds=0,
    )

    assert subsystem.operational is None
    assert _classify(subsystem).state is not FMC
    assert _classify(subsystem).confidence is LOW


def test_explicit_null_subsystem_operational_flag_is_missing_telemetry():
    subsystem = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "operational": None, "mission_critical_fault": False, "telemetry_age_seconds": 0}
    )

    assert (_classify(subsystem).state, _classify(subsystem).confidence) == (PMC, LOW)


_NON_BOOLEAN_FLAGS = [0, 1, "yes", "no", "true", "false", 1.0, "", [], {}]
_NON_BOOLEAN_IDS = [
    "int-0", "int-1", "str-yes", "str-no", "str-true", "str-false",
    "float-1", "empty-str", "list", "dict",
]


@pytest.mark.parametrize("flag", ["mission_critical_fault", "operational"])
@pytest.mark.parametrize("value", _NON_BOOLEAN_FLAGS, ids=_NON_BOOLEAN_IDS)
def test_non_boolean_subsystem_flag_is_not_coerced_by_validation(flag, value):
    record = {**_REPORTED_SUBSYSTEM, "mission_critical_fault": False, "telemetry_age_seconds": 0}
    record[flag] = value

    subsystem = Subsystem.model_validate(record)
    result = _classify(_sub("A"), subsystem)

    assert getattr(subsystem, flag) is None
    assert result.state is not FMC
    assert (result.state, result.confidence) == (PMC, LOW)


@pytest.mark.parametrize("value", _NON_BOOLEAN_FLAGS, ids=_NON_BOOLEAN_IDS)
def test_non_boolean_platform_operational_flag_is_not_coerced_by_validation(value):
    platform = Platform.model_validate(
        {
            "platform_id": "TST-002",
            "designation": "Test Platform 002",
            "platform_type": "LAND",
            "operational": value,
            "subsystems": [
                {**_REPORTED_SUBSYSTEM, "mission_critical_fault": False, "telemetry_age_seconds": 0}
            ],
        }
    )

    result = classify_readiness(platform)
    summary = get_platform_summary(platform)

    assert platform.operational is None
    assert (result.state, result.confidence) == (PMC, LOW)
    assert summary["operational"] is False


def test_real_boolean_flags_are_trusted_through_validation():
    subsystem = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "mission_critical_fault": False, "telemetry_age_seconds": 0}
    )

    assert subsystem.operational is True
    assert subsystem.mission_critical_fault is False
    assert (_classify(subsystem).state, _classify(subsystem).confidence) == (FMC, HIGH)


def test_malformed_fault_flag_with_real_fault_elsewhere_is_nmc_low():
    malformed = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "mission_critical_fault": "no", "telemetry_age_seconds": 0}
    )

    result = _classify(_sub("A", mission_critical_fault=True), malformed)

    assert (result.state, result.confidence) == (NMC, LOW)


@pytest.mark.parametrize("operational", [None, "yes", 1])
def test_unknown_subsystem_operational_flag_is_published_as_false(operational):
    subsystem = Subsystem.model_validate(
        {**_REPORTED_SUBSYSTEM, "operational": operational, "mission_critical_fault": False, "telemetry_age_seconds": 0}
    )

    summary = get_platform_summary(_platform(subsystems=[subsystem]))

    assert summary["subsystems"][0]["operational"] is False
    assert (summary["readinessState"], summary["readinessConfidence"]) == ("PMC", "LOW")


@pytest.mark.parametrize(
    "bad",
    [
        {"temperature_celsius": None},
        {"temperature_celsius": math.nan},
        {"temperature_celsius": math.inf},
        {"temperature_celsius": -math.inf},
        {"telemetry_age_seconds": 300},
        {"telemetry_age_seconds": -5},
        {"telemetry_age_seconds": None},
        {"mission_critical_fault": None},
        {"operational": None},
        {"operational": 1},
        {"mission_critical_fault": 0},
    ],
)
def test_bad_telemetry_never_yields_fmc(bad):
    assert _classify(_sub(**bad)).state is not FMC


def test_confidence_is_low_when_state_is_nmc_and_telemetry_is_bad():
    result = _classify(
        _sub("A", mission_critical_fault=True),
        _sub("B", telemetry_age_seconds=3600),
    )

    assert (result.state, result.confidence) == (NMC, LOW)


def test_stale_high_reading_still_counts_for_rule_2():
    result = _classify(_sub(temperature_celsius=95.0, telemetry_age_seconds=3600))

    assert (result.state, result.confidence) == (NMC, LOW)


def test_stale_warm_reading_still_counts_for_rule_4():
    result = _classify(_sub(temperature_celsius=80.0, telemetry_age_seconds=3600))

    assert (result.state, result.confidence) == (PMC, LOW)


@pytest.mark.parametrize("temperature", [math.nan, -math.inf], ids=["nan", "minus-inf"])
def test_nan_or_minus_inf_reading_does_not_trigger_temperature_rules(temperature):
    result = _classify(_sub("A", temperature_celsius=20.0), _sub("B", temperature_celsius=temperature))

    assert (result.state, result.confidence) == (PMC, LOW)


def test_plus_inf_reading_triggers_rule_2():
    result = _classify(_sub("A", temperature_celsius=20.0), _sub("B", temperature_celsius=math.inf))

    assert (result.state, result.confidence) == (NMC, LOW)


def test_classification_is_deterministic():
    platform = _platform(
        subsystems=[_sub("A", temperature_celsius=75.0), _sub("B", temperature_celsius=None)]
    )

    assert {classify_readiness(platform) for _ in range(5)} == {classify_readiness(platform)}


@pytest.mark.parametrize(
    ("platform_id", "state", "confidence"),
    [
        ("LND-114", "FMC", "HIGH"),
        ("AIR-207", "PMC", "HIGH"),
        ("MSN-330", "NMC", "LOW"),
    ],
)
def test_fleet_classification(platform_id, state, confidence):
    summary = get_platform_summary(get_platform(platform_id))

    assert summary["readinessState"] == state
    assert summary["readinessConfidence"] == confidence


def test_summary_publishes_readiness_fields_as_plain_strings():
    summary = get_platform_summary(_platform())

    assert type(summary["readinessState"]) is str
    assert type(summary["readinessConfidence"]) is str
    assert (summary["readinessState"], summary["readinessConfidence"]) == ("FMC", "HIGH")


def test_summary_platform_fields_are_rev_c_plus_rev_d_readiness():
    assert set(get_platform_summary(_platform())) == {
        "platformId",
        "designation",
        "platformType",
        "operational",
        "subsystems",
        "readinessState",
        "readinessConfidence",
    }


@pytest.mark.parametrize(
    ("temperature", "state"),
    [(math.nan, "PMC"), (math.inf, "NMC"), (-math.inf, "PMC")],
    ids=["nan", "plus-inf", "minus-inf"],
)
def test_summary_publishes_non_finite_temperature_as_null(temperature, state):
    platform = _platform(subsystems=[_sub(temperature_celsius=temperature)])

    summary = get_platform_summary(platform)

    assert summary["subsystems"][0]["temperatureCelsius"] is None
    assert summary["readinessState"] == state
    assert summary["readinessConfidence"] == "LOW"


def test_summary_never_exposes_classification_internals():
    summary = get_platform_summary(
        _platform(subsystems=[_sub(mission_critical_fault=True, telemetry_age_seconds=3600)])
    )
    flattened = repr(summary)

    for leaked in (
        "missionCriticalFault",
        "telemetryAgeSeconds",
        "mission_critical_fault",
        "telemetry_age_seconds",
        "PHM-RDY-1",
        "rule",
        "reason",
    ):
        assert leaked not in flattened
