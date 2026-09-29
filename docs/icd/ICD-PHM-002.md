# ICD-PHM-002 — Sustainment API external interface

| Field | Value |
|---|---|
| Document | ICD-PHM-002 |
| Revision | **D (draft — pending Interface Control Board approval)** |
| Status | Proposed. Rev C remains baselined until rev D is approved. |
| Owner | Interface Control Board |
| Service version | PHMS 2.3.0 |
| Machine-readable form | `GET /openapi.json` |
| Readiness rule | `PHM-RDY-1` |

This is a **controlled interface document**. Any change to the public API
payload is an interface change and requires a revision of this document plus a
consumer impact assessment before merge.

## Revision history

| Rev | Change | Requirement | Status |
|---|---|---|---|
| A | Initial platform list endpoint | SYS-4400 | Superseded |
| B | Added platform detail endpoint and subsystem array | SYS-4400 | Superseded |
| C | Added `platformType`; baselined subsystem field set | SYS-4400 | Baselined — superseded on rev D approval |
| D | Added derived `readinessState` and `readinessConfidence` to the platform record (rule `PHM-RDY-1`); non-finite `temperatureCelsius` published as `null` | SYS-4412 | **Draft — awaiting ICB approval** |

## Consumers

| Consumer | Schema validation | Impact sensitivity |
|---|---|---|
| Maintenance planning | Strict | High — rejects undeclared fields |
| Sortie generation | Lenient | Medium |
| Availability reporting | Lenient | Medium — figures are contractual |
| Customer sustainment portal | Strict | High |

Two consumers validate strictly. An additive field is therefore **not**
automatically non-breaking.

## Consumer impact statement (rev C → rev D)

Rev D adds two fields to every platform record. It removes and renames nothing.
Every rev C field keeps its name, type and nullability. One rev C behaviour
changes, recorded below.

**Non-finite `temperatureCelsius` is now published as `null`.** At rev C a
non-finite subsystem reading (NaN, +infinity or −infinity) had no defined JSON
representation and could not be serialised. At rev D it is treated as
unavailable and published as `null`, the value rev C already permits for an
unavailable reading. The field's type and nullability are unchanged, but a
consumer may now receive `null` for a subsystem whose raw reading exists and is
non-finite. Consumers that treat `null` as "no reading" need no change.
Consumers must not infer that a `null` temperature means the subsystem is cool;
`readinessConfidence` is `LOW` whenever this happens.

| Consumer | Impact | Action required before rev D is deployed |
|---|---|---|
| Maintenance planning | **Breaking.** Strict validation rejects the two new fields. Non-finite readings arrive as `null`. | Update schema to rev D. Confirm `null` temperature handling. Coordinated deployment. |
| Customer sustainment portal | **Breaking.** Strict validation rejects the two new fields. Non-finite readings arrive as `null`. | Update schema to rev D. Confirm `null` temperature handling. Coordinated deployment. |
| Sortie generation | Non-breaking. Lenient validation ignores unknown fields. Non-finite readings arrive as `null`. | Adopt `readinessState` in place of local derivation (recommended). |
| Availability reporting | Non-breaking. Figures are contractual. Non-finite readings arrive as `null`. | Confirm `PHM-RDY-1` matches the SYS-4400 contracted availability definition before adopting. **Alignment unverified.** |

Rollout is coordinated, not opt-in. Rev D must not be deployed until both
strict consumers accept rev D payloads. Rollback is a redeploy of the rev C
service, which removes both fields from any consumer that has adopted them.

## Endpoints

### `GET /platforms`

Returns an array of platform records. `200 OK`.

### `GET /platforms/{platform_id}`

Returns a single platform record. `200 OK`, or `404 Not Found` with
`{"detail": "Platform not found"}`.

## Platform record

| Field | Type | Nullable | Since | Description |
|---|---|---|---|---|
| `platformId` | string | No | A | Fleet-unique platform identifier |
| `designation` | string | No | A | Human-readable platform designation |
| `platformType` | string | No | C | `LAND`, `AIR` or `MISSION_SYSTEM` |
| `operational` | boolean | No | A | Platform-level operational flag |
| `subsystems` | array | No | B | Subsystem records, order significant |
| `readinessState` | string | No | D | `FMC`, `PMC` or `NMC`, derived by rule `PHM-RDY-1` |
| `readinessConfidence` | string | No | D | `HIGH` or `LOW`. `LOW` when any subsystem telemetry is missing, stale, malformed or non-finite |

Both rev D fields are present on every platform record, on both endpoints. No
other fields are permitted at rev D.

## Subsystem record

Field set, types and nullability unchanged from rev C. Rev D changes the
publication of non-finite `temperatureCelsius` readings: they are now published
as `null` (see the consumer impact statement).

| Field | Type | Nullable | Description |
|---|---|---|---|
| `subsystemId` | string | No | Platform-unique subsystem identifier |
| `name` | string | No | Subsystem name |
| `temperatureCelsius` | number | **Yes** | Most recent reading; `null` when unavailable. **Rev D:** a non-finite reading (NaN, ±infinity) is unavailable and is published as `null`. |
| `operational` | boolean | No | Subsystem-level operational flag |

## Readiness derivation — rule `PHM-RDY-1`

Traceability: SYS-4412, parent SYS-4400. Implemented once, in
`classify_readiness()` in `src/readiness_service.py`. Both endpoints use it.

Classification is advisory decision-support output. The rule is evaluated per
platform. The first matching precedence wins.

| Precedence | Condition | `readinessState` |
|---|---|---|
| 1 | Any subsystem has a mission-critical fault | `NMC` |
| 2 | Any valid subsystem temperature >= 90.0 °C | `NMC` |
| 3 | Platform not operational, or any subsystem not operational | `NMC` |
| 4 | Any valid subsystem temperature >= 70.0 °C and < 90.0 °C | `PMC` |
| 5 | *Reserved.* Degraded but mission-capable. No degraded signal is specified yet, so this rule never matches. | `PMC` |
| 6 | Telemetry missing, stale, malformed or non-finite for any subsystem, or no subsystems reported | `PMC` |
| 7 | Otherwise: all subsystems nominal and operational | `FMC` |

`readinessConfidence` is evaluated separately from precedence. It is `LOW`
whenever any telemetry is bad, whatever the state, including `NMC`. Otherwise
it is `HIGH`.

Definitions:

- **Valid temperature** — a finite number. Rules 2 and 4 use valid readings
  even when they are stale, so an old high reading is never discarded in the
  platform's favour.
- **Missing** — no temperature reading (`null`), or no reported telemetry age
  or mission-critical fault flag for the subsystem. An absent age is never
  treated as fresh, and an absent fault flag is never treated as "no fault".
- **Non-finite** — NaN, +infinity or −infinity.
- **Malformed** — a temperature or telemetry age that is not a number, a
  negative telemetry age, or a fault flag that is not a boolean.
- **Stale** — telemetry age of **300 seconds or more**. A reading exactly
  300 seconds old is stale.

Boundary behaviour:

| Highest valid temperature | `readinessState` (no other rule matching) |
|---|---|
| 69.9 °C | `FMC` |
| 70.0 °C | `PMC` (rule 4) |
| 89.9 °C | `PMC` (rule 4) |
| 90.0 °C | `NMC` (rule 2) |

Missing, stale, malformed or non-finite telemetry never yields `FMC`.

The rule version `PHM-RDY-1` is published here, not in the payload. Any change
to the precedence, thresholds or definitions above requires a new rule version
and a new ICD revision.

Thresholds are synthetic. Alignment of `PHM-RDY-1` with the SYS-4400
contracted availability definition is **unverified** and is recorded as a
residual risk.

## Excluded from the interface

The following internal state is held by the service and **must not** be
exposed:

- `mission_critical_fault` — internal fault indication
- `telemetry_age_seconds` — internal telemetry staleness
- The matched precedence rule and any classification reasons
- Stack traces, exception detail, fault codes, internal diagnostics

## Example

`GET /platforms/LND-114`

```json
{
  "platformId": "LND-114",
  "designation": "Recovery Vehicle 114",
  "platformType": "LAND",
  "operational": true,
  "subsystems": [
    {
      "subsystemId": "PWR-01",
      "name": "Powerpack",
      "temperatureCelsius": 64.0,
      "operational": true
    },
    {
      "subsystemId": "HYD-01",
      "name": "Hydraulic System",
      "temperatureCelsius": 51.0,
      "operational": true
    }
  ],
  "readinessState": "FMC",
  "readinessConfidence": "HIGH"
}
```

## Conformance

`tests/contract/test_icd_phm_002_compatibility.py` asserts the rev C field set
exactly, on both endpoints. It runs as a separately named CI step
(`ICD contract tests`) so an interface violation is visibly distinct from an
ordinary test failure.

This test must never be weakened or deleted to make a change pass. A failure is
an interface-change escalation, not a test defect.

The rev D implementation fails this test by design. The Interface Control Board
updates `tests/contract/` to the rev D field set after approving this revision.
Until then the contract failure is the recorded escalation.

## Open interface changes

| Requirement | Proposed change | Status |
|---|---|---|
| SYS-4412 | Add derived `readinessState` and `readinessConfidence` to the platform record | Rev D drafted — awaiting ICB approval and contract-test update |
