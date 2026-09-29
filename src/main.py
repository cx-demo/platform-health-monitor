from fastapi import FastAPI, HTTPException

from src.readiness_service import get_platform_summary
from src.repository import get_platform, list_platforms

app = FastAPI(
    title="Platform Health & Mission Readiness Service",
    version="2.3.0",
)


@app.get("/platforms")
def retrieve_platforms():
    return [get_platform_summary(item) for item in list_platforms()]


@app.get("/platforms/{platform_id}")
def retrieve_platform_by_id(platform_id: str):
    platform = get_platform(platform_id)

    if platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")

    return get_platform_summary(platform)
