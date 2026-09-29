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

Observed on the baseline pull request, after the repository was made public
and code scanning was reconfigured:

| Required check | Result | Note |
|---|---|---|
| `Unit, integration and contract tests` | ✅ Pass | 20 tests, coverage gate met |
| `Requirement Traceability` | ✅ Pass | Requirement ID, matrix update and evidence all present |
| `CodeQL analysis` | ✅ Pass | `security-extended,security-and-quality`, SARIF ingested |
| `Dependency Review` | ✅ Pass | `fail-on-severity: moderate` |

## Security configuration

| Feature | State |
|---|---|
| Repository visibility | Public |
| Code scanning (CodeQL, advanced setup) | Enabled |
| CodeQL default setup | Disabled — required, see below |
| Secret scanning | Enabled |
| Secret scanning push protection | Enabled |
| Dependency graph | Enabled |
| Dependabot security updates | Enabled |

### CodeQL default setup had to be disabled

With default setup enabled, the SARIF produced by
`.github/workflows/codeql.yml` was rejected:

```
Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled
```

Default setup was set to `not-configured` so the **versioned, reviewable**
workflow in the repository is the authoritative scanning configuration. That
matters here: the query suite (`security-extended`) is part of the change
record, not a setting somebody toggled in the UI.

## Code ownership

`CODEOWNERS` resolves with no errors
(`GET /repos/{owner}/{repo}/codeowners/errors` → `{"errors": []}`).

| Path | Owner | Role |
|---|---|---|
| `/src/`, `/.github/workflows/`, `/.github/rulesets/` | `@cx-demo` | Engineering authority |
| `/docs/icd/`, `/tests/contract/` | `@pedric1` | Interface control board |

The implementing engineer cannot approve their own interface change.

## Unverified at baseline

The following are **unverified** and are explicitly labelled as such:

- Ruleset enforcement and blocked-merge behaviour — `.github/rulesets/main-protection.json`
  has not yet been applied to the repository. Apply it after this baseline
  merges, then confirm an administrator merge is actually refused.
