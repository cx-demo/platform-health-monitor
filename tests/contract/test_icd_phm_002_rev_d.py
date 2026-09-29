"""
ICD-PHM-002 rev D conformance for the /v2 surface (SYS-4412).

Rev D is published only on /v2/platforms and /v2/platforms/{platform_id}.
Strict-schema consumers validate this payload, so additional undeclared
fields are a breaking change. The field set below is checked against the
rev D platform record table in docs/icd/ICD-PHM-002.md, so the controlled
document and this test cannot drift apart. The rev C surface is covered,
unchanged, by test_icd_phm_002_compatibility.py.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

ICD_PATH = Path(__file__).resolve().parents[2] / "docs" / "icd" / "ICD-PHM-002.md"
REV_D_TABLE_HEADING = "## Platform record — rev D (`/v2/platforms`)"

ICD_PHM_002_REV_D_PLATFORM_FIELDS = {
    "platformId",
    "designation",
    "platformType",
    "operational",
    "subsystems",
    "readinessState",
    "readinessConfidence",
}

ICD_READINESS_STATES = {"FMC", "PMC", "NMC"}
ICD_READINESS_CONFIDENCE = {"HIGH", "LOW"}


def _icd_rev_d_platform_record_fields():
    text = ICD_PATH.read_text(encoding="utf-8")
    assert text.count(REV_D_TABLE_HEADING) == 1
    section = text.split(REV_D_TABLE_HEADING, 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\|\s*`([A-Za-z]+)`\s*\|", section, flags=re.MULTILINE))


def _v2_records():
    listed = client.get("/v2/platforms")
    assert listed.status_code == 200
    records = listed.json()
    assert records
    details = []
    for record in records:
        detail = client.get(f"/v2/platforms/{record['platformId']}")
        assert detail.status_code == 200
        details.append(detail.json())
    return records, details


def test_icd_declares_exactly_the_rev_d_contract_field_set():
    assert _icd_rev_d_platform_record_fields() == ICD_PHM_002_REV_D_PLATFORM_FIELDS


def test_v2_detail_endpoint_matches_icd_rev_d_exactly():
    response = client.get("/v2/platforms/LND-114")

    assert response.status_code == 200
    assert set(response.json().keys()) == ICD_PHM_002_REV_D_PLATFORM_FIELDS


def test_v2_list_endpoint_matches_icd_rev_d_exactly():
    listed, details = _v2_records()

    for record in listed + details:
        assert set(record.keys()) == ICD_PHM_002_REV_D_PLATFORM_FIELDS


def test_v2_readiness_fields_use_only_icd_values():
    listed, details = _v2_records()

    for record in listed + details:
        assert record["readinessState"] in ICD_READINESS_STATES
        assert record["readinessConfidence"] in ICD_READINESS_CONFIDENCE


def test_v2_openapi_publishes_rev_d_version():
    document = client.get("/v2/openapi.json").json()

    assert document["info"]["version"] == "2.4.0"
