# Risk register

Scope: Platform Health & Mission Readiness Service (PHMS).

Severity: `Low` · `Medium` · `High` · `Critical`.
Status: `Open` · `Mitigated` · `Accepted` · `Closed`.

Residual risk acceptance requires a **named** engineering authority. No agent
may self-accept a risk.

## Baseline risks (SYS-4400)

| ID | Risk | Severity | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| RSK-1 | Downstream consumers each derive platform usability from raw telemetry, producing divergent availability figures for the same platform | High | SYS-4412 introduces a single authoritative derivation | Fleet Availability WG | Open |
| RSK-2 | Internal fault and telemetry-staleness fields are leaked through the public API | Medium | Projection in `readiness_service.get_platform_summary` excludes them; asserted by unit tests | Engineering authority | Mitigated |
| RSK-3 | Strict-schema consumers break when the payload gains a field | High | ICD-PHM-002 is controlled; contract suite is a required check; `tests/contract/` is CODEOWNER-protected | Interface Control Board | Mitigated |
| RSK-4 | Telemetry may be absent, stale or non-finite; the current API passes it through without qualification | Medium | Consumers currently interpret raw values; SYS-4412 must never yield a favourable state on incomplete data | Fleet Availability WG | Open |

## Risks arising from SYS-4412

Recorded by the safety and security workstream during implementation. No
entries at baseline.

| ID | Risk | Severity | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Residual risk acceptance

| Risk | Accepted by | Role | Date | Rationale |
|---|---|---|---|---|
| — | — | — | — | — |
