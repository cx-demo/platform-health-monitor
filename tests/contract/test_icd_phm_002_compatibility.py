"""
ICD-PHM-002 rev C conformance.

Downstream sustainment planning consumes this payload under a strict
schema contract. Additional undeclared fields are a breaking change
for consumers that validate strictly. Any schema change requires an
ICD revision and a consumer impact assessment before merge.
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

ICD_PHM_002_PLATFORM_FIELDS = {
    "platformId",
    "designation",
    "platformType",
    "operational",
    "subsystems",
}


def test_detail_endpoint_matches_icd_exactly():
    response = client.get("/platforms/LND-114")

    assert response.status_code == 200
    assert set(response.json().keys()) == ICD_PHM_002_PLATFORM_FIELDS


def test_list_endpoint_matches_icd_exactly():
    response = client.get("/platforms")

    assert response.status_code == 200
    for record in response.json():
        assert set(record.keys()) == ICD_PHM_002_PLATFORM_FIELDS
