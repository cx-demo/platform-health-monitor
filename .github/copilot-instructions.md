# Repository engineering instructions

## Architecture

- API transport logic stays in src/main.py.
- Domain and classification logic stays in src/readiness_service.py.
- Data models stay in src/models.py.
- No business rules inside route handlers.

## Interface control

- docs/icd/ICD-PHM-002.md is a controlled interface document.
- Any change to the public API payload is an interface change.
- Interface changes require an ICD revision and a consumer impact statement.
- Never modify tests/contract/ to accommodate a change. If a contract test
  fails, treat it as an interface-change escalation, not a test defect.

## Quality

- Preserve existing public API fields.
- Add tests for every boundary value and failure condition.
- Never weaken, skip or delete an existing test to obtain a passing result.
- Run unit, integration and contract tests before declaring work complete.
- Prefer small, readable changes over broad refactoring.

## Safety and security

- Never report a more favourable readiness state than the evidence supports.
- Missing, stale, malformed or non-finite telemetry must never yield FMC.
- Do not expose stack traces, fault codes or internal diagnostics via the API.
- Record unresolved safety, security or compatibility concerns rather than
  resolving them silently.

## Traceability

- Every change must reference its requirement ID.
- Update docs/traceability-matrix.md when requirement coverage changes.
- Update docs/icd/ICD-PHM-002.md when the public API changes.
- Update docs/risk-register.md when a change introduces material risk.
- Write session evidence to docs/evidence/ as committed files, not chat output.

## Evidence discipline

- Do not claim a test, check, scan or review passed without linking evidence.
- Label anything unverified as unverified.
