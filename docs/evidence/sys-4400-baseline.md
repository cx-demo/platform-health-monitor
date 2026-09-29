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

## Continuous integration result

Observed on the baseline pull request:

| Required check | Result | Note |
|---|---|---|
| `Unit, integration and contract tests` | ✅ Pass | 20 tests, coverage gate met |
| `Requirement Traceability` | ✅ Pass | Requirement ID, matrix update and evidence all present |
| `CodeQL analysis` | ❌ Fail | Analysis completed; **SARIF upload rejected — code scanning not enabled on the repository** |
| `Dependency Review` | ❌ Fail | **Not supported — dependency review requires GHAS on a private repository** |

## Blocked: GitHub Advanced Security not licensed

`cx-demo/platform-health-monitor` is **private** and GHAS has not been purchased
for the organisation. Confirmed by API response:

```
PATCH /repos/cx-demo/platform-health-monitor
  security_and_analysis[advanced_security][status]=enabled
→ 422 "Advanced security has not been purchased."
```

Consequence: code scanning, secret scanning, push protection and dependency
review cannot be enabled, and two of the four required status checks in
`.github/rulesets/main-protection.json` cannot pass.

Enabled successfully:

- Dependency graph
- Dependabot security updates

Resolution requires one of the following, by a repository or organisation
administrator:

1. Assign GHAS (Code Security and Secret Protection) to this repository; or
2. Make the repository public, where code scanning and dependency review are
   free.

The failing checks have deliberately **not** been removed, weakened or made
non-blocking. A required check that cannot pass is a licensing fact to be
resolved, not a gate to be lowered.

## Unverified at baseline

The following are **unverified** and are explicitly labelled as such:

- CodeQL findings — analysis ran but results could not be ingested, so no
  finding set exists for this baseline.
- Dependency review — never executed.
- Secret scanning and push protection — not available.
- Ruleset enforcement and blocked-merge behaviour — requires repository
  administrator application of `.github/rulesets/main-protection.json`.
