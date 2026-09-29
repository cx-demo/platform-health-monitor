import math

from src.models import (
    Platform,
    ReadinessAssessment,
    ReadinessConfidence,
    ReadinessState,
    Subsystem,
)

# SYS-4412: rule version published in ICD-PHM-002 rev D, not in the payload.
READINESS_RULE_VERSION = "PHM-RDY-1"

NMC_TEMPERATURE_CELSIUS = 90.0
PMC_TEMPERATURE_CELSIUS = 70.0
STALE_TELEMETRY_AGE_SECONDS = 300


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_temperature(subsystem: Subsystem) -> float | None:
    value = subsystem.temperature_celsius
    if _is_number(value) and math.isfinite(value):
        return float(value)
    return None


def _has_bad_telemetry(subsystem: Subsystem) -> bool:
    """Missing, non-finite, malformed or stale telemetry (PHM-RDY-1 rule 6)."""
    if _valid_temperature(subsystem) is None:
        return True
    age = subsystem.telemetry_age_seconds
    if not _is_number(age) or not math.isfinite(age) or age < 0:
        return True
    return age >= STALE_TELEMETRY_AGE_SECONDS


def classify_readiness(platform: Platform) -> ReadinessAssessment:
    """Apply rule PHM-RDY-1 (SYS-4412). First matching precedence wins."""
    subsystems = platform.subsystems
    temperatures = [
        t for t in (_valid_temperature(s) for s in subsystems) if t is not None
    ]
    bad_telemetry = not subsystems or any(_has_bad_telemetry(s) for s in subsystems)
    confidence = (
        ReadinessConfidence.LOW if bad_telemetry else ReadinessConfidence.HIGH
    )

    if any(s.mission_critical_fault for s in subsystems):
        state = ReadinessState.NMC
    elif any(t >= NMC_TEMPERATURE_CELSIUS for t in temperatures):
        state = ReadinessState.NMC
    elif not platform.operational or any(not s.operational for s in subsystems):
        state = ReadinessState.NMC
    elif any(t >= PMC_TEMPERATURE_CELSIUS for t in temperatures):
        state = ReadinessState.PMC
    # Rule 5 (degraded but mission-capable) is reserved: no degraded signal
    # is specified, so it never matches.
    elif bad_telemetry:
        state = ReadinessState.PMC
    else:
        state = ReadinessState.FMC

    return ReadinessAssessment(state=state, confidence=confidence)


def get_platform_summary(platform: Platform) -> dict:
    readiness = classify_readiness(platform)
    return {
        "platformId": platform.platform_id,
        "designation": platform.designation,
        "platformType": platform.platform_type,
        "operational": platform.operational,
        "subsystems": [
            {
                "subsystemId": s.subsystem_id,
                "name": s.name,
                "temperatureCelsius": _valid_temperature(s),
                "operational": s.operational,
            }
            for s in platform.subsystems
        ],
        "readinessState": readiness.state.value,
        "readinessConfidence": readiness.confidence.value,
    }
