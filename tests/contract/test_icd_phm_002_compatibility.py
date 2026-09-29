"""
ICD-PHM-002 rev D conformance.

Downstream sustainment planning consumes this payload under a strict
schema contract. Additional undeclared fields are a breaking change
for consumers that validate strictly. Any schema change requires an
ICD revision and a consumer impact assessment before merge.

Rev D (SYS-4412) adds the derived ``readinessState`` and
``readinessConfidence`` fields. The field set below is checked against the
Platform record table in docs/icd/ICD-PHM-002.md, so the controlled document
and this test cannot drift apart.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

ICD_PATH = Path(__file__).resolve().parents[2] / "docs" / "icd" / "ICD-PHM-002.md"

ICD_PHM_002_PLATFORM_FIELDS = {
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


def _icd_platform_record_fields():
    text = ICD_PATH.read_text(encoding="utf-8")
    section = text.split("## Platform record", 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\|\s*`([A-Za-z]+)`\s*\|", section, flags=re.MULTILINE))


def test_icd_declares_exactly_the_contract_field_set():
    assert _icd_platform_record_fields() == ICD_PHM_002_PLATFORM_FIELDS


def test_detail_endpoint_matches_icd_exactly():
    response = client.get("/platforms/LND-114")

    assert response.status_code == 200
    assert set(response.json().keys()) == ICD_PHM_002_PLATFORM_FIELDS


def test_list_endpoint_matches_icd_exactly():
    response = client.get("/platforms")

    assert response.status_code == 200
    for record in response.json():
        assert set(record.keys()) == ICD_PHM_002_PLATFORM_FIELDS


def test_readiness_fields_use_only_icd_values():
    listed = client.get("/platforms").json()
    detail = [client.get(f"/platforms/{r['platformId']}").json() for r in listed]

    for record in listed + detail:
        assert record["readinessState"] in ICD_READINESS_STATES
        assert record["readinessConfidence"] in ICD_READINESS_CONFIDENCE
