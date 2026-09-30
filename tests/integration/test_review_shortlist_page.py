"""
SYS-4419 — static guards for the Figure 4 maintenance review shortlist.

Behaviour is proven in the browser suite (tests/browser/). These checks hold
properties of the shipped page that must stay true whatever the browser does:
the API surface is untouched, no handling marking is invented, no readiness
class is named, and no raw error text is echoed to the page.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import STATIC_DIR, app

client = TestClient(app)

DASHBOARD = Path(STATIC_DIR) / "dashboard.html"


def _markup() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def test_served_dashboard_carries_the_review_shortlist():
    markup = client.get("/dashboard").text

    assert "Figure 4 · Maintenance review shortlist" in markup
    assert 'id="review-threshold"' in markup
    assert 'id="review-export"' in markup


def test_published_interface_paths_are_unchanged():
    document = client.get("/openapi.json").json()

    assert set(document["paths"]) == {"/platforms", "/platforms/{platform_id}"}


def test_handling_marking_is_not_invented():
    match = re.search(r'<meta name="phm-handling-marking" content="([^"]*)">', _markup())

    assert match is not None, "the export needs one place to read the approved marking from"
    assert match.group(1) == "", (
        "the handling marking must be the data-owner-approved wording recorded on #12; "
        "until then the page ships it empty and export stays disabled"
    )


def test_page_names_no_readiness_class():
    assert re.search(r"\b(FMC|PMC|NMC)\b", _markup()) is None


def test_page_does_not_echo_raw_error_text():
    markup = _markup()

    assert "error.message" not in markup
    assert "error.stack" not in markup


def test_threshold_has_no_default_value():
    tag = re.search(r"<input[^>]*id=\"review-threshold\"[^>]*>", _markup(), re.S)

    assert tag is not None
    assert "value=" not in tag.group(0)
    assert "required" in tag.group(0)
