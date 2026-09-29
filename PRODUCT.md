# Product

<!-- impeccable:product-schema 1 -->

> **Interview status.** The structured question probe returned "user unavailable" before any
> round was answered. Every fact below is therefore drawn from the repository, the governing
> demo runbook, and the explicit brief. Facts that are **inferred** rather than confirmed are
> marked `[inferred]` and should be corrected on the first available review.

## Platform

web

## Users

Systems, software and safety engineers working on a defence / aerospace fleet-sustainment
programme. They read this service's output while assessing whether individual platforms are fit
to be tasked, and they work inside a controlled-change regime where an interface is a contract,
not an implementation detail.

Secondary audience `[inferred]`: engineering managers and interface-control-board reviewers who
need to see the consequence of an interface gap without reading Python.

## Product Purpose

The Platform Health & Mission Readiness Service (PHMS) publishes the health of land, air and
mission-system platforms across a deployed fleet over a controlled interface, ICD-PHM-002.

It exists so that tasking decisions are made against one agreed, versioned view of platform
health rather than against whatever each consumer happens to scrape.

Success is that a consumer of ICD-PHM-002 can correctly decide whether a platform may be
tasked, using only fields the contract actually publishes.

## Positioning

The interface is the product. PHMS is not valuable because it stores telemetry; it is valuable
because ICD-PHM-002 is a governed, revision-controlled contract that downstream mission systems
can build against and that no single team may change unilaterally.

## Operating Context

- FastAPI service; `GET /platforms` and `GET /platforms/{platform_id}` return summaries shaped by
  `src/readiness_service.get_platform_summary`. OpenAPI is generated at `/openapi.json`, with
  Swagger UI at `/docs` and ReDoc at `/redoc`.
- The published summary is a deliberate **projection** of the internal model. `Subsystem` carries
  `mission_critical_fault` and `telemetry_age_seconds`; `get_platform_summary` omits both.
- Change is governed. Work is traced by `SYS-NNNN` requirement IDs. Every pull request must carry
  a requirement ID. Requirement-to-test coverage, risks and evidence links are recorded in the
  issue or pull request for human review.
  `main` is protected by an active ruleset; code ownership is split so that `/docs/icd/` and
  `/tests/contract/` sit with the interface-control board.
- `tests/contract/test_icd_phm_002_compatibility.py` asserts the ICD-PHM-002 revision D field set
  exactly on both endpoints and checks it against the ICD Platform record table. It is a
  governance instrument. Weakening, skipping or deleting it to make a build pass is the defined
  wrong answer; when an ICD revision changes the payload, it is updated to that revision in the
  same pull request, at least as strictly, with code-owner approval of both.
- SYS-4412 adds derived `readinessState` (`FMC` / `PMC` / `NMC`) and `readinessConfidence`
  (`HIGH` / `LOW`) to every platform record under rule `PHM-RDY-1`. It advances ICD-PHM-002 to
  revision D, which is drafted and awaits Interface Control Board approval of both the ICD and
  the contract tests.

## Capabilities and Constraints

**Confirmed capabilities**

- Three platforms in a fixed in-memory fleet: `LND-114` (LAND), `AIR-207` (AIR),
  `MSN-330` (MISSION_SYSTEM). Each carries two subsystems with a temperature reading.
- Per-platform and whole-fleet retrieval. Unknown identifiers return HTTP 404.

**Constraints that bind any new work**

- **The published contract grows only by ICD revision.** Any surface built on PHMS reads only
  the ICD-PHM-002 revision D field set: `platformId`, `designation`, `platformType`,
  `operational`, `readinessState`, `readinessConfidence`, and per subsystem `subsystemId`,
  `name`, `temperatureCelsius`, `operational`. Rendering any other field, or any field before
  its ICD revision exists, is forbidden.
- Read-only. No control actions, no write paths, no tasking authority.
- Test coverage on `src/` is gated at 90%. New Python needs matching tests.
- No network fonts or third-party CDNs; the service must run air-gapped `[inferred]`.

**Known contract gap, narrowed at revision D**

`MSN-330` has a mission-critical fault on its prime power generator and comms telemetry one hour
stale. Neither field is published, and the platform's own `operational` flag reads `true`. At
revision C any consumer honouring the contract would report `MSN-330` as serviceable. Revision D
publishes `readinessState: NMC` and `readinessConfidence: LOW` for it. The fault and the
telemetry age remain unpublished, and that remaining gap stays visible.

## Brand Commitments

The service is titled "Platform Health & Mission Readiness Service", version 2.3.0, as declared
in `src/main.py`. Platform and subsystem identifiers are fixed vocabulary and appear verbatim.

## Evidence on Hand

- Real fleet data in `src/repository.py` — synthetic for demonstration, but it is the only fleet
  this product has, and it is authored, not placeholder.
- Interface and architecture documents: `docs/icd/ICD-PHM-002.md` (revision D draft),
  `docs/architecture.md`.
- Engineering change request: `demo/sys-4412-issue.md`.

No customers, benchmarks, deployment claims, pricing or certifications exist. None may be
invented — including implied ones such as fake timestamps presented as live telemetry, airfield
names, or operator identities.

## Product Principles

1. **The contract is the product.** What the interface publishes is the whole truth available to
   a consumer. Surfaces render the contract; they never reach behind it.
2. **Make the gap visible, do not close it.** Where the contract is insufficient, the honest move
   is to show the insufficiency and raise a change, not to paper over it locally.
3. **Traceable before complete.** Work that cannot be traced to a requirement and evidenced is
   not deliverable here, however good it looks.
4. **Never weaken a control to make a build green.** Failing gates are findings.
5. **Read-only means read-only.** This product informs a decision; it never takes one.

## Accessibility & Inclusion

`[inferred]` No programme-specific standard has been stated. Treat WCAG 2.2 AA as the working
floor: status must never be carried by colour alone, all text must meet contrast minimums, and
the surface must be fully keyboard navigable. Colour-blind safety is a live concern for any
red/amber/green convention in this domain.
