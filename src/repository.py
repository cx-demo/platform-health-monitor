from src.models import Platform, Subsystem


PLATFORMS = {
    "LND-114": Platform(
        platform_id="LND-114",
        designation="Recovery Vehicle 114",
        platform_type="LAND",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="PWR-01",
                name="Powerpack",
                temperature_celsius=64.0,
            ),
            Subsystem(
                subsystem_id="HYD-01",
                name="Hydraulic System",
                temperature_celsius=51.0,
            ),
        ],
    ),
    "AIR-207": Platform(
        platform_id="AIR-207",
        designation="Rotary Platform 207",
        platform_type="AIR",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="GBX-01",
                name="Main Gearbox",
                temperature_celsius=78.0,
            ),
            Subsystem(
                subsystem_id="AVN-01",
                name="Mission Avionics",
                temperature_celsius=42.0,
            ),
        ],
    ),
    "MSN-330": Platform(
        platform_id="MSN-330",
        designation="Deployable Mission System 330",
        platform_type="MISSION_SYSTEM",
        operational=True,
        subsystems=[
            Subsystem(
                subsystem_id="GEN-01",
                name="Prime Power Generator",
                temperature_celsius=94.0,
                mission_critical_fault=True,
            ),
            Subsystem(
                subsystem_id="COM-01",
                name="Comms Suite",
                temperature_celsius=55.0,
                telemetry_age_seconds=3600,
            ),
        ],
    ),
}


def get_platform(platform_id: str) -> Platform | None:
    return PLATFORMS.get(platform_id)


def list_platforms() -> list[Platform]:
    return list(PLATFORMS.values())
