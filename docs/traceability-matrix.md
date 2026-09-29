# Requirement traceability matrix

Generated from the repository. One row per acceptance criterion:
requirement → implementation → test evidence → assurance → status.

`docs/traceability-matrix.md` must be updated by any pull request that changes
requirement coverage. The `Requirement Traceability` workflow enforces this.

## SYS-4400 — Fleet Availability Reporting (baseline)

| AC | Requirement | Implementation | Test evidence | Assurance | Status |
|---|---|---|---|---|---|
| AC-4400-1 | Sustainment API exposes the platform fleet | `main.py::retrieve_platforms` | `test_platform_api.py::test_list_endpoint_returns_every_platform` | ICD rev C | ✅ Verified |
| AC-4400-2 | Sustainment API exposes a single platform by identifier | `main.py::retrieve_platform_by_id` | `test_platform_api.py::test_detail_endpoint_returns_requested_platform` | ICD rev C | ✅ Verified |
| AC-4400-3 | Unknown platform returns 404 without diagnostics | `main.py::retrieve_platform_by_id` | `test_platform_api.py::test_detail_endpoint_returns_404_for_unknown_platform`, `::test_detail_error_does_not_leak_internal_diagnostics` | RSK-2 | ✅ Verified |
| AC-4400-4 | Payload conforms exactly to the ICD-PHM-002 rev C field set | `readiness_service.py::get_platform_summary` | `test_icd_phm_002_compatibility.py` (both endpoints) | ICD rev C, RSK-3 | ✅ Verified |
| AC-4400-5 | Internal fault and telemetry-age state is never exposed | `readiness_service.py::get_platform_summary` | `test_readiness_service.py::test_summary_never_exposes_internal_diagnostics` | RSK-2 | ✅ Verified |
| AC-4400-6 | List and detail payloads are consistent | `readiness_service.py::get_platform_summary` | `test_platform_api.py::test_list_and_detail_payloads_are_consistent` | — | ✅ Verified |
| AC-4400-7 | Generated OpenAPI document matches the published interface | `main.py` route signatures | `test_platform_api.py::test_openapi_document_is_served` | ICD rev C; served at `/docs`, `/redoc`, `/openapi.json` | ✅ Verified |
| AC-4400-8 | The pull request boundary is enforced, not conventional | `.github/rulesets/main-protection.json` | Direct push to `main` rejected — `push declined due to repository rule violations` | Ruleset `main-engineering-governance` active | ✅ Verified |

Evidence: `docs/evidence/sys-4400-baseline.md`

## SYS-4412 — Derived platform readiness state

Not implemented. `readinessState` does not exist in this codebase.

| AC | Requirement | Implementation | Test evidence | Assurance | Status |
|---|---|---|---|---|---|
| AC-1 | `readinessState` on both endpoints | — | — | — | ⏳ Not started |
| AC-2 | Permitted values exactly FMC, PMC, NMC | — | — | — | ⏳ Not started |
| AC-3 | Precedence applied deterministically and documented | — | — | — | ⏳ Not started |
| AC-4 | Boundaries verified at 69.9 / 70.0 / 89.9 / 90.0 °C | — | — | — | ⏳ Not started |
| AC-5 | Missing, stale, malformed or non-finite telemetry never yields FMC | — | — | RSK-4 | ⏳ Not started |
| AC-6 | All existing ICD-PHM-002 fields preserved | — | — | RSK-3 | ⏳ Not started |
| AC-7 | Interface change assessed; ICD revised if payload shape changes | — | — | ICD rev D required | ⏳ Not started |
| AC-8 | Unit, integration and contract tests pass without modifying existing assertions | — | — | — | ⏳ Not started |
| AC-9 | Requirement-to-test traceability recorded | — | — | — | ⏳ Not started |
| AC-10 | Residual risk accepted by a named engineering authority | — | — | — | ⏳ Not started |
