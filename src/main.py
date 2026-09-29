from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from src.readiness_service import get_platform_summary, summarise_v2
from src.repository import get_platform, list_platforms

app = FastAPI(
    title="Platform Health & Mission Readiness Service",
    version="2.3.0",
)

# SYS-4412: ICD-PHM-002 rev D surface. Mounted beside the frozen rev C paths
# so consumers opt in by base path; it publishes its own /v2/openapi.json.
v2 = FastAPI(
    title="Platform Health & Mission Readiness Service",
    version="2.4.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


# The fleet plate is a presentation surface, not part of the controlled
# interface. It is excluded from the generated OpenAPI document so that
# /openapi.json continues to describe exactly the ICD-PHM-002 rev C
# surface and nothing else. Publishing it would be an interface change.
@app.get("/", include_in_schema=False)
def redirect_to_dashboard():
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", include_in_schema=False)
def retrieve_dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html", media_type="text/html")


@app.get("/platforms")
def retrieve_platforms():
    return [get_platform_summary(item) for item in list_platforms()]


@app.get("/platforms/{platform_id}")
def retrieve_platform_by_id(platform_id: str):
    platform = get_platform(platform_id)

    if platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")

    return get_platform_summary(platform)


@v2.get("/platforms")
def retrieve_platforms_v2():
    return [summarise_v2(item) for item in list_platforms()]


@v2.get("/platforms/{platform_id}")
def retrieve_platform_by_id_v2(platform_id: str):
    platform = get_platform(platform_id)

    if platform is None:
        raise HTTPException(status_code=404, detail="Platform not found")

    return summarise_v2(platform)


app.mount("/v2", v2)
