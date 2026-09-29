# Evidence — SYS-4400 baseline

| Field | Value |
|---|---|
| Requirement | SYS-4400 — Fleet Availability Reporting |
| Scope | PHMS 2.3.0 service baseline |
| Interface | ICD-PHM-002 rev C |
| Workstream | Repository baseline |

## Purpose of this file

`docs/evidence/` is the cross-session evidence surface. Sessions run in isolated
worktrees and cannot read each other's chat; committed evidence files are the
only reliable shared input to consolidation, and the `Requirement Traceability`
required check fails when this directory is empty.

This file establishes that baseline.

## Verification performed

Local execution against the service baseline, Python 3.12+, editable install
with the `dev` extra.

| Suite | Command | Result |
|---|---|---|
| Unit | `pytest tests/unit` | 9 passed |
| Integration | `pytest tests/integration` | 9 passed |
| ICD contract | `pytest tests/contract` | 2 passed |
| Coverage gate | `pytest --cov=src --cov-fail-under=90` | 100% on `src/`, gate met |

The same four steps run in `.github/workflows/ci.yml` under the check context
`Unit, integration and contract tests`. The contract suite is a separately
named step so an interface violation reads differently from a build failure.

## Interface conformance

`GET /platforms` and `GET /platforms/{platform_id}` return exactly the
ICD-PHM-002 rev C field set:
`platformId`, `designation`, `platformType`, `operational`, `subsystems`.

Asserted by `tests/contract/test_icd_phm_002_compatibility.py`.

## Confirmed absences

- `readinessState` does not exist anywhere in `src/` or `tests/`. SYS-4412 is
  not implemented.
- Internal diagnostics `mission_critical_fault` and `telemetry_age_seconds` are
  not projected onto the public payload.
- The 404 response carries no stack trace or internal path detail.

## Unverified at baseline

The following are **unverified** and are explicitly labelled as such:

- CodeQL analysis — no run recorded against this baseline yet.
- Dependency review — runs on pull requests only.
- Ruleset enforcement and blocked-merge behaviour — requires repository
  administrator application of `.github/rulesets/main-protection.json`.
- GHAS secret scanning, push protection and Dependabot alerts — require
  repository administrator enablement.
