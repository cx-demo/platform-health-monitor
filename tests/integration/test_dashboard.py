"""
SYS-4418 — fleet plate (read-only dashboard).

The plate is a presentation surface built on top of the published interface.
These tests hold three boundaries:

1.  It is served and reachable.
2.  It is NOT part of the controlled interface, so the generated OpenAPI
    documents still describe exactly the ICD-PHM-002 rev C surface (root)
    and the rev D surface (/v2).
3.  It renders only fields the interface it reads (/v2, rev D, SYS-4412)
    actually publishes. Internal
    subsystem state is derived from the model at run time rather than
    written out here, so this assertion keeps working if the model grows
    and never restates an internal field name in the test suite.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.main import STATIC_DIR, app
from src.models import Platform, Subsystem
from src.readiness_service import summarise_v2
from src.repository import list_platforms

client = TestClient(app)

DASHBOARD = Path(STATIC_DIR) / "dashboard.html"


def _camel(snake: str) -> str:
    head, *rest = snake.split("_")
    return head + "".join(part.title() for part in rest)


def _published_field_names() -> set[str]:
    summary = summarise_v2(list_platforms()[0])
    names = set(summary)
    for subsystem in summary["subsystems"]:
        names |= set(subsystem)
    return names


def _internal_only_field_names() -> set[str]:
    modelled = set(Platform.model_fields) | set(Subsystem.model_fields)
    return {_camel(field) for field in modelled} - _published_field_names()


def test_dashboard_is_served():
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_root_redirects_to_the_dashboard():
    response = client.get("/", follow_redirects=False)

    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/dashboard"


def test_dashboard_is_not_part_of_the_published_interface():
    document = client.get("/openapi.json").json()

    assert "/dashboard" not in document["paths"]
    assert "/" not in document["paths"]
    assert set(document["paths"]) == {"/platforms", "/platforms/{platform_id}"}


def test_dashboard_is_not_part_of_the_v2_interface():
    document = client.get("/v2/openapi.json").json()

    assert set(document["paths"]) == {"/platforms", "/platforms/{platform_id}"}


def test_dashboard_renders_only_published_fields():
    markup = DASHBOARD.read_text(encoding="utf-8")
    internal_only = _internal_only_field_names()

    assert internal_only, "expected the model to hold state the interface withholds"
    for field in internal_only:
        assert field not in markup, (
            f"the fleet plate references {field!r}, which the interface does not "
            "publish; a presentation surface must not reach behind the contract"
        )


def test_dashboard_consumes_the_published_field_set():
    markup = DASHBOARD.read_text(encoding="utf-8")

    for field in _published_field_names():
        assert field in markup


def test_dashboard_requests_no_third_party_origin():
    markup = DASHBOARD.read_text(encoding="utf-8")

    assert 'src="http' not in markup
    assert 'href="http' not in markup
    assert "@import" not in markup


def test_dashboard_reads_the_v2_surface_only():
    markup = DASHBOARD.read_text(encoding="utf-8")

    assert "fetch('/v2/platforms'" in markup
    assert "href=\"/v2/platforms/'" in markup
    assert "fetch('/platforms'" not in markup
    assert "href=\"/platforms/" not in markup


def test_dashboard_renders_readiness_as_neutral_text():
    markup = DASHBOARD.read_text(encoding="utf-8")
    rule = markup.split(".row__readiness {", 1)[1].split("}", 1)[0]

    assert "color: var(--ink);" in rule
    for styled in ("background", "border", "--warn", "--alert", "red", "amber", "green"):
        assert styled not in rule
