from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel


class Subsystem(BaseModel):
    subsystem_id: str
    name: str
    temperature_celsius: float | None = None
    operational: bool = True
    # SYS-4412: None means the value was not reported. Absence is missing
    # telemetry under PHM-RDY-1 rule 6, never "no fault" or "fresh".
    mission_critical_fault: bool | None = None
    telemetry_age_seconds: int | None = None


class Platform(BaseModel):
    platform_id: str
    designation: str
    platform_type: str
    operational: bool
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
