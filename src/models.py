from pydantic import BaseModel


class Subsystem(BaseModel):
    subsystem_id: str
    name: str
    temperature_celsius: float | None = None
    operational: bool = True
    mission_critical_fault: bool = False
    telemetry_age_seconds: int = 0


class Platform(BaseModel):
    platform_id: str
    designation: str
    platform_type: str
    operational: bool
    subsystems: list[Subsystem]
