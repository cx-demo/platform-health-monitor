from src.models import Platform


def get_platform_summary(platform: Platform) -> dict:
    return {
        "platformId": platform.platform_id,
        "designation": platform.designation,
        "platformType": platform.platform_type,
        "operational": platform.operational,
        "subsystems": [
            {
                "subsystemId": s.subsystem_id,
                "name": s.name,
                "temperatureCelsius": s.temperature_celsius,
                "operational": s.operational,
            }
            for s in platform.subsystems
        ],
    }
