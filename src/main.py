from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse

from src.readiness_service import get_platform_summary
from src.repository import get_platform, list_platforms

app = FastAPI(
    title="Platform Health & Mission Readiness Service",
    version="2.3.0",
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
