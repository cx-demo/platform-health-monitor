# Evidence — SYS-4418 read-only fleet visualisation plate

| Field | Value |
|---|---|
| Requirement | SYS-4418 — Read-only fleet visualisation plate |
| Scope | Presentation surface served at `GET /dashboard` |
| Interface | ICD-PHM-002 rev C — **unchanged** |
| Workstream | Visualisation |

## Interface impact assessment

**No interface change. No ICD revision required.**

The plate is a browser-side consumer of the same public payload any other
integrator receives. It is served by the same process purely as a convenience;
it holds no privileged access, performs no server-side projection of its own,
and reads exactly one endpoint, `GET /platforms`.

Both presentation routes are registered with `include_in_schema=False`.
`/openapi.json` is the machine-readable form of ICD-PHM-002, so adding a path to
it would itself constitute an interface change. The published document therefore
still describes exactly the two contract endpoints it described at revision C,
which `tests/contract/test_icd_phm_002_compatibility.py` continues to assert
without modification.

## What the plate can and cannot show

The plate renders the published field set and nothing else. Because
`readiness_service.get_platform_summary` strips `mission_critical_fault` and
`telemetry_age_seconds` before serialisation, those readings are not merely
hidden by the presentation layer — they never reach it.

This is verifiable rather than asserted. `MSN-330/GEN-01` carries a
mission-critical fault at 94 °C and `MSN-330/COM-01` carries telemetry one hour
old; the plate can show the temperature, because temperature is published, but
it cannot show the fault, the staleness, or any readiness conclusion, because
revision C publishes no field that carries them. Figure 3 records those three
unanswerable questions explicitly as reserved, unpublished space.

`readinessState` appears nowhere in `src/` or `tests/`.

## Verification performed

Local execution, editable install with the `dev` extra.

| Suite | Command | Result |
|---|---|---|
| Full suite | `pytest` | 26 passed |
| Dashboard integration | `pytest tests/integration/test_dashboard.py` | 6 passed |
| ICD contract (unmodified) | `pytest tests/contract` | 2 passed |
| Coverage gate | `pytest --cov=src --cov-fail-under=90` | 100% on `src/`, gate met |

### Governance assertions under test

| Assertion | Test |
|---|---|
| Surface is served | `test_dashboard_is_served` |
| Root directs to the surface | `test_root_redirects_to_the_dashboard` |
| Surface is absent from the published interface | `test_dashboard_is_not_part_of_the_published_interface` |
| Surface names only published fields | `test_dashboard_renders_only_published_fields` |
| Surface consumes the full published field set | `test_dashboard_consumes_the_published_field_set` |
| No third-party origin is contacted | `test_dashboard_requests_no_third_party_origin` |

`test_dashboard_renders_only_published_fields` derives the internal-only field
set at runtime from the Pydantic models rather than hard-coding field names, so
the suite asserts the boundary without writing the forbidden identifiers into
the repository.

## Deployment constraints honoured

The surface is a single self-contained file: markup, CSS, JavaScript and SVG are
all inline, there are no webfonts and no third-party requests of any kind. It is
therefore serviceable in an air-gapped environment, which the deployment context
assumes.

## Accessibility and presentation verification

Rendered and inspected at 1440 px and 390 px viewport widths with
`prefers-reduced-motion` forced, confirming that no content depends on motion to
become visible and that the narrow layout neither overflows nor clips.

Serviceability is encoded as a **mark** — a filled versus outlined sign, plus
text — not as a hue, so the status reading does not depend on colour vision. All
foreground/background pairs meet WCAG AA contrast.
