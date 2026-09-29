import math

from src.models import (
    Platform,
    ReadinessAssessment,
    ReadinessConfidence,
    ReadinessState,
    Subsystem,
)

# SYS-4412: rule version published in ICD-PHM-002 rev D, not in the payload.
READINESS_RULE_VERSION = "SYS-4412-R1"

NMC_TEMPERATURE_CELSIUS = 90.0
PMC_TEMPERATURE_CELSIUS = 70.0
ABSOLUTE_ZERO_CELSIUS = -273.15
# Telemetry older than this many seconds is stale; exactly 300 s is fresh.
STALE_TELEMETRY_AGE_SECONDS = 300


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_temperature(subsystem: Subsystem) -> float | None:
    """Finite reading at or above absolute zero; anything else is unusable."""
    value = subsystem.temperature_celsius
    if _is_number(value) and math.isfinite(value) and value >= ABSOLUTE_ZERO_CELSIUS:
        return float(value)
    return None


def _reads_at_or_above(subsystem: Subsystem, threshold: float) -> bool:
    """Finite or +inf reading at or above threshold. NaN and -inf never match."""
    value = subsystem.temperature_celsius
    return _is_number(value) and not math.isnan(value) and value >= threshold


def _has_bad_telemetry(subsystem: Subsystem) -> bool:
    """Missing, non-finite, malformed or stale telemetry (SYS-4412-R1 rule 6)."""
    if _valid_temperature(subsystem) is None:
        return True
    if not isinstance(subsystem.operational, bool):
        return True
    if not isinstance(subsystem.mission_critical_fault, bool):
        return True
    age = subsystem.telemetry_age_seconds
    if not _is_number(age):
        return True
    try:
        if not math.isfinite(age):
            return True
    except OverflowError:
        # An int too large to convert to a float is malformed, never an error.
        return True
    if age < 0:
        return True
    return age > STALE_TELEMETRY_AGE_SECONDS


def classify_readiness(platform: Platform) -> ReadinessAssessment:
    """Apply rule SYS-4412-R1. First matching precedence wins."""
    subsystems = platform.subsystems
    bad_telemetry = (
        not subsystems
        or not isinstance(platform.operational, bool)
        or any(_has_bad_telemetry(s) for s in subsystems)
    )
    confidence = (
        ReadinessConfidence.LOW if bad_telemetry else ReadinessConfidence.HIGH
    )

    if any(s.mission_critical_fault is True for s in subsystems):
        state = ReadinessState.NMC
    elif any(_reads_at_or_above(s, NMC_TEMPERATURE_CELSIUS) for s in subsystems):
        state = ReadinessState.NMC
    elif platform.operational is False:
        state = ReadinessState.NMC
    elif any(_reads_at_or_above(s, PMC_TEMPERATURE_CELSIUS) for s in subsystems):
        state = ReadinessState.PMC
    elif any(s.operational is False for s in subsystems):
        # Rule 5: a subsystem reporting not operational is degraded but
        # mission-capable.
        state = ReadinessState.PMC
    elif bad_telemetry:
        state = ReadinessState.PMC
    else:
        state = ReadinessState.FMC

    return ReadinessAssessment(state=state, confidence=confidence)


def get_platform_summary(platform: Platform) -> dict:
    """ICD-PHM-002 rev C platform record, served on /platforms. No readiness."""
    return {
        "platformId": platform.platform_id,
        "designation": platform.designation,
        "platformType": platform.platform_type,
        # An unreported or malformed flag is never published as true.
        "operational": platform.operational is True,
        "subsystems": [
            {
                "subsystemId": s.subsystem_id,
                "name": s.name,
                "temperatureCelsius": _valid_temperature(s),
                "operational": s.operational is True,
            }
            for s in platform.subsystems
        ],
    }


def summarise_v2(platform: Platform) -> dict:
    """ICD-PHM-002 rev D platform record, served on /v2 only (SYS-4412)."""
    readiness = classify_readiness(platform)
    return {
        **get_platform_summary(platform),
        "readinessState": readiness.state.value,
        "readinessConfidence": readiness.confidence.value,
    }
