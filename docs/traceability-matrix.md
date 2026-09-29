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

Evidence: `docs/evidence/sys-4400-baseline.md`

## SYS-4418 — Read-only fleet visualisation plate

A browser-side presentation surface served at `GET /dashboard`. It is a consumer
of ICD-PHM-002 revision C, not an extension of it: the interface is unchanged and
no ICD revision is required.

| AC | Requirement | Implementation | Test evidence | Assurance | Status |
|---|---|---|---|---|---|
| AC-4418-1 | A visualisation surface is served to operators | `main.py::serve_dashboard` | `test_dashboard.py::test_dashboard_is_served` | — | ✅ Verified |
| AC-4418-2 | Service root directs to the visualisation surface | `main.py::serve_root` | `test_dashboard.py::test_root_redirects_to_the_dashboard` | — | ✅ Verified |
| AC-4418-3 | Presentation routes are excluded from the published interface | `main.py` (`include_in_schema=False`) | `test_dashboard.py::test_dashboard_is_not_part_of_the_published_interface` | ICD rev C, RSK-3 | ✅ Verified |
| AC-4418-4 | The surface renders only ICD-PHM-002 rev C published fields | `static/dashboard.html` | `test_dashboard.py::test_dashboard_renders_only_published_fields`, `::test_dashboard_consumes_the_published_field_set` | ICD rev C, RSK-2 | ✅ Verified |
| AC-4418-5 | The surface is read-only and holds no privileged access | `static/dashboard.html` (`fetch('/platforms')` only) | `test_dashboard.py::test_dashboard_consumes_the_published_field_set` | RSK-2 | ✅ Verified |
| AC-4418-6 | No third-party origin is contacted (air-gapped deployment) | `static/dashboard.html` (inline CSS/JS/SVG, no webfonts) | `test_dashboard.py::test_dashboard_requests_no_third_party_origin` | RSK-2 | ✅ Verified |
| AC-4418-7 | The interface is unchanged; no ICD revision required | — | `test_icd_phm_002_compatibility.py` (unmodified, still passing) | ICD rev C | ✅ Verified |

Evidence: `docs/evidence/sys-4418-dashboard.md`

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
