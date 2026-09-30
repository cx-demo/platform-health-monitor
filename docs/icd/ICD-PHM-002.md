# ICD-PHM-002 — Sustainment API external interface

| Field | Value |
|---|---|
| Document | ICD-PHM-002 |
| Revision | **D (draft — pending Interface Control Board approval)** |
| Status | Proposed. Rev C remains baselined for `/platforms` and is not changed by rev D. |
| Owner | Interface Control Board |
| Service version | PHMS 2.3.0 (rev C, `/platforms`) · PHMS 2.4.0 (rev D, `/v2/platforms`) |
| Machine-readable form | `GET /openapi.json` (rev C, `info.version` 2.3.0) · `GET /v2/openapi.json` (rev D, `info.version` 2.4.0) |
| Readiness rule | `SYS-4412-R1` |

This is a **controlled interface document**. Any change to the public API
payload is an interface change and requires a revision of this document plus a
consumer impact assessment before merge.

Rev D is published as a **parallel surface** under the `/v2` base path. The rev C
paths (`/platforms`, `/platforms/{platform_id}`) keep the rev C field set and
carry no readiness fields. Consumers opt in to rev D by switching base path.

## Revision history

| Rev | Change | Requirement | Status |
|---|---|---|---|
| A | Initial platform list endpoint | SYS-4400 | Superseded |
| B | Added platform detail endpoint and subsystem array | SYS-4400 | Superseded |
| C | Added `platformType`; baselined subsystem field set | SYS-4400 | **Baselined** — current for `/platforms` |
| D | Added `/v2/platforms` and `/v2/platforms/{platform_id}` (PHMS 2.4.0). Their platform record is the rev C record plus derived `readinessState` and `readinessConfidence` (rule `SYS-4412-R1`). Rev C paths unchanged. | SYS-4412 | **Draft — awaiting ICB approval** |

## Consumers

| Consumer | Schema validation | Impact sensitivity |
|---|---|---|
| Maintenance planning | Strict | High — rejects undeclared fields |
| Sortie generation | Lenient | Medium |
| Availability reporting | Lenient | Medium — figures are contractual |
| Customer sustainment portal | Strict | High |

Two consumers validate strictly. An additive field is therefore **not**
automatically non-breaking. Rev D adds its fields only on the new `/v2` paths
for that reason.

## Consumer impact statement (rev C → rev D)

Rev D adds two paths and two fields on those paths. It removes and renames
nothing. The rev C paths keep the rev C field set, types and nullability, and
the root `/openapi.json` stays at `info.version` 2.3.0. No consumer is affected
until it chooses to call `/v2`.

| Consumer | Impact | Action required |
|---|---|---|
| Maintenance planning | None while it stays on `/platforms`. Opt-in: strict validation must adopt the rev D record before switching to `/v2`. | Adopt the rev D schema, then switch base path to `/v2`. |
| Customer sustainment portal | None while it stays on `/platforms`. Opt-in: strict validation must adopt the rev D record before switching to `/v2`. | Adopt the rev D schema, then switch base path to `/v2`. |
| Sortie generation | None while it stays on `/platforms`. Lenient validation accepts the rev D record. | Switch to `/v2` and use `readinessState` in place of local derivation (recommended). |
| Availability reporting | None while it stays on `/platforms`. Figures are contractual. | Confirm `SYS-4412-R1` matches the SYS-4400 contracted availability definition, then switch to `/v2`. **Alignment unverified.** |

Until every consumer uses `/v2`, the fleet may still carry divergent readiness
figures (RR-5). Rollback is removal of the `/v2` mount; the rev C paths are not
touched by rev D or by its rollback.

**Requirement-owner decision (SYS-4412 AC1).** The requirement owner accepted
`GET /v2/platforms` and `GET /v2/platforms/{platform_id}` as meeting the
"list and detail endpoints" wording of SYS-4412 acceptance criterion 1.

## Endpoints

### Rev C — `GET /platforms`

Returns an array of rev C platform records. `200 OK`.

### Rev C — `GET /platforms/{platform_id}`

Returns a single rev C platform record. `200 OK`, or `404 Not Found` with
`{"detail": "Platform not found"}`.

### Rev D — `GET /v2/platforms`

Returns an array of rev D platform records, in the same order as
`GET /platforms`. `200 OK`.

### Rev D — `GET /v2/platforms/{platform_id}`

Returns a single rev D platform record. `200 OK`, or `404 Not Found` with
`{"detail": "Platform not found"}`.

## Platform record — rev C (`/platforms`)

| Field | Type | Nullable | Description |
|---|---|---|---|
| `platformId` | string | No | Fleet-unique platform identifier |
| `designation` | string | No | Human-readable platform designation |
| `platformType` | string | No | `LAND`, `AIR` or `MISSION_SYSTEM` |
| `operational` | boolean | No | Platform-level operational flag |
| `subsystems` | array | No | Subsystem records, order significant |

No other fields are permitted at rev C.

## Platform record — rev D (`/v2/platforms`)

| Field | Type | Nullable | Since | Description |
|---|---|---|---|---|
| `platformId` | string | No | A | Fleet-unique platform identifier |
| `designation` | string | No | A | Human-readable platform designation |
| `platformType` | string | No | C | `LAND`, `AIR` or `MISSION_SYSTEM` |
| `operational` | boolean | No | A | Platform-level operational flag |
| `subsystems` | array | No | B | Subsystem records, order significant |
| `readinessState` | string | No | D | `FMC`, `PMC` or `NMC`, derived by rule `SYS-4412-R1` |
| `readinessConfidence` | string | No | D | `HIGH` or `LOW`. `LOW` when any telemetry is missing, stale, malformed or non-finite |

The first five fields are identical in name, type, nullability and value to the
rev C record for the same platform. Both rev D fields are present on every
record, on both `/v2` endpoints. No other fields are permitted at rev D.

## Subsystem record (both revisions)

| Field | Type | Nullable | Description |
|---|---|---|---|
| `subsystemId` | string | No | Platform-unique subsystem identifier |
| `name` | string | No | Subsystem name |
| `temperatureCelsius` | number | **Yes** | Most recent reading; `null` when unavailable |
| `operational` | boolean | No | Subsystem-level operational flag |

**Publication of unusable telemetry (both revisions).** A temperature that is
missing, non-finite, non-numeric or below −273.15 °C is unavailable and is
published as `null`. An operational flag that is unreported or not a real
boolean is published as `false`, never `true`. Types and nullability are
unchanged. For every platform the service currently holds, the rev C payload
is unchanged from PHMS 2.3.0.

## Readiness derivation — rule `SYS-4412-R1`

Traceability: SYS-4412, parent SYS-4400. Implemented once, in
`classify_readiness()` in `src/readiness_service.py`. Used only by the `/v2`
endpoints.

Classification is advisory decision-support output. The rule is evaluated per
platform. The first matching precedence wins.

| Precedence | Condition | `readinessState` |
|---|---|---|
| 1 | Any subsystem has a mission-critical fault | `NMC` |
| 2 | Any subsystem temperature ≥ 90.0 °C (valid or +infinity) | `NMC` |
| 3 | Platform reported not operational (`false`) | `NMC` |
| 4 | Any valid subsystem temperature ≥ 70.0 °C and < 90.0 °C | `PMC` |
| 5 | Any subsystem reported not operational (`false`): degraded but mission-capable | `PMC` |
| 6 | Telemetry missing, stale, malformed or non-finite for any subsystem, platform operational flag malformed, or no subsystems reported | `PMC` |
| 7 | Otherwise: all subsystems nominal and operational, with valid fresh telemetry | `FMC` |

`readinessConfidence` is evaluated separately from precedence. It is `LOW`
whenever the rule 6 condition holds, whatever the state, including `NMC`.
Otherwise it is `HIGH`.

Definitions:

- **Valid temperature** — a finite number at or above −273.15 °C. Rules 2 and 4
  use valid readings even when they are stale, so an old high reading is never
  discarded in the platform's favour.
- **Missing** — no temperature reading (`null`), or no reported telemetry age,
  mission-critical fault flag or operational flag. An absent age is never
  treated as fresh, an absent fault flag never as "no fault", and an absent
  operational flag never as operational.
- **Non-finite** — NaN, +infinity or −infinity. +infinity is a reading at or
  above 90.0 °C, so rule 2 applies (`NMC`). NaN and −infinity fall to rule 6.
- **Malformed** — never coerced; held as unreported and can match only rule 6:
  - a temperature that is `null`, non-finite, non-numeric (for example a
    boolean or a string such as `"95"`), or below −273.15 °C;
  - a telemetry age that is a boolean, a string, a fractional or non-finite
    number, an integer too large to convert to floating point, or negative.
    A floating-point age holding a finite whole number (for example `300.0`)
    is used as that whole number of seconds;
  - a platform or subsystem fault or operational flag that is not a real
    boolean (for example `0`, `1`, `"yes"` or `"false"`).
- **Stale** — telemetry age **above 300 seconds**. A reading exactly 300
  seconds old is fresh; 301 seconds is stale.

Boundary behaviour:

| Input (no other rule matching) | `readinessState` |
|---|---|
| Highest valid temperature 69.9 °C | `FMC` |
| Highest valid temperature 70.0 °C | `PMC` (rule 4) |
| Highest valid temperature 89.9 °C | `PMC` (rule 4) |
| Highest valid temperature 90.0 °C | `NMC` (rule 2) |
| Telemetry age 300 s | `FMC` |
| Telemetry age 301 s | `PMC` (rule 6, `LOW`) |
| Temperature −273.15 °C | `FMC` |
| Temperature −273.16 °C | `PMC` (rule 6, `LOW`) |

Missing, stale, malformed or non-finite telemetry never yields `FMC`.

The rule version `SYS-4412-R1` is published here, not in the payload. The
service does not log individual classifications; an audit reproduces a
classification from the recorded telemetry and this rule version. Any change to
the precedence, thresholds or definitions above requires a new rule version and
a new ICD revision.

Thresholds are synthetic. Alignment of `SYS-4412-R1` with the SYS-4400
contracted availability definition is **unverified** (RR-2).

## Residual risks (rev D)

Each risk is **pending acceptance by @pedric1** (Interface Control Board, named
engineering authority). None is accepted yet.

| ID | Risk | Behaviour at rev D | Acceptance |
|---|---|---|---|
| RR-1 | A missing, NaN, −infinity, below −273.15 °C or otherwise malformed temperature cannot detect overheating. A subsystem actually at or above 90.0 °C that reports no usable reading is classified `PMC`, not `NMC`. | Rule 6: `PMC`, `LOW` unless an earlier rule matches; temperature published as `null`. | Pending @pedric1 |
| RR-2 | `SYS-4412-R1` may diverge from the SYS-4400 contracted availability definition, which is held outside this repository. | Alignment unverified; thresholds synthetic. | Pending @pedric1 |
| RR-3 | An unreported or malformed `operational` flag is published as `false`. For a platform flag, the record is classified `PMC` by rule 6, while a consumer re-deriving readiness from the published `false` would reach `NMC` (rule 3). | Published `false`; `PMC`, `LOW` unless an earlier rule matches. | Pending @pedric1 |
| RR-4 | A malformed mission-critical fault flag is held as unreported, not as a fault. A subsystem with a real fault but a malformed flag is classified `PMC`, not `NMC`. | Rule 6: `PMC`, `LOW` unless an earlier rule matches. | Pending @pedric1 |
| RR-5 | Consumers may stay on rev C `/platforms`, which carries no readiness. Divergent readiness figures persist until every consumer moves to `/v2`, and two surfaces must be maintained until rev C is retired. | Rev D is opt-in; rev C unchanged. | Pending @pedric1 |

## Excluded from the interface

The following internal state is held by the service and **must not** be
exposed on either surface:

- `mission_critical_fault` — internal fault indication
- `telemetry_age_seconds` — internal telemetry staleness
- The matched precedence rule, the rule version and any classification reasons
- Stack traces, exception detail, fault codes, internal diagnostics

## Example

`GET /platforms/LND-114` (rev C)

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
  ]
}
```

`GET /v2/platforms/LND-114` (rev D)

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
exactly, on both rev C endpoints. It is unchanged by rev D.

`tests/contract/test_icd_phm_002_rev_d.py` asserts the rev D field set exactly,
on both `/v2` endpoints, and checks that `readinessState` and
`readinessConfidence` carry only the values this document permits. It also
checks that the field set it asserts matches the
[rev D platform record](#platform-record--rev-d-v2platforms) table above, so
this document and the test cannot drift apart.

Both run in the separately named CI step (`ICD contract tests`) so an interface
violation is visibly distinct from an ordinary test failure. They must never be
weakened, skipped or deleted to make a change pass. A failure against an
unrevised ICD is an interface-change escalation, not a test defect.

## Open interface changes

| Requirement | Proposed change | Status |
|---|---|---|
| SYS-4412 | Publish derived `readinessState` and `readinessConfidence` on a parallel `/v2` rev D surface | Rev D drafted — awaiting ICB approval |
