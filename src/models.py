import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _untrusted_flag_to_none(value: object) -> object:
    # SYS-4412: only a real boolean is trusted. Anything else (0, 1, "yes",
    # "false") is malformed telemetry and is held as None rather than being
    # coerced into a trusted True/False.
    return value if isinstance(value, bool) else None


def _untrusted_temperature_to_none(value: object) -> object:
    # SYS-4412: only a real int or float is a reading. A bool or a string
    # ("85.0", "inf") is malformed telemetry, held as None, never coerced.
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return None


def _untrusted_age_to_none(value: object) -> object:
    # SYS-4412: an age is a real number of whole seconds. An int, or a float
    # holding a finite whole number (10.0), is kept. A bool, string, fractional
    # or non-finite float is malformed telemetry, held as None, never coerced.
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return None


# None means not reported or malformed: missing telemetry under PHM-RDY-1
# rule 6, never "operational", "no fault" or "fresh".
TelemetryFlag = Annotated[bool | None, BeforeValidator(_untrusted_flag_to_none)]
TelemetryTemperature = Annotated[
    float | None, BeforeValidator(_untrusted_temperature_to_none)
]
TelemetryAge = Annotated[int | None, BeforeValidator(_untrusted_age_to_none)]


class Subsystem(BaseModel):
    subsystem_id: str
    name: str
    temperature_celsius: TelemetryTemperature = None
    operational: TelemetryFlag = None
    mission_critical_fault: TelemetryFlag = None
    telemetry_age_seconds: TelemetryAge = None


class Platform(BaseModel):
    platform_id: str
    designation: str
    platform_type: str
    operational: TelemetryFlag
    subsystems: list[Subsystem]


class ReadinessState(StrEnum):
    """SYS-4412 readiness values published at ICD-PHM-002 rev D."""

    FMC = "FMC"
    PMC = "PMC"
    NMC = "NMC"


class ReadinessConfidence(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


@dataclass(frozen=True)
class ReadinessAssessment:
    state: ReadinessState
    confidence: ReadinessConfidence
