# ICD-PHM-002 — Sustainment API external interface

| Field | Value |
|---|---|
| Document | ICD-PHM-002 |
| Revision | **C** |
| Status | Baselined |
| Owner | Interface Control Board |
| Service version | PHMS 2.3.0 |
| Machine-readable form | `GET /openapi.json` |

This is a **controlled interface document**. Any change to the public API
payload is an interface change and requires a revision of this document plus a
consumer impact assessment before merge.

## Revision history

| Rev | Change | Requirement | Status |
|---|---|---|---|
| A | Initial platform list endpoint | SYS-4400 | Superseded |
| B | Added platform detail endpoint and subsystem array | SYS-4400 | Superseded |
| C | Added `platformType`; baselined subsystem field set | SYS-4400 | **Current** |

## Consumers

| Consumer | Schema validation | Impact sensitivity |
|---|---|---|
| Maintenance planning | Strict | High — rejects undeclared fields |
| Sortie generation | Lenient | Medium |
| Availability reporting | Lenient | Medium — figures are contractual |
| Customer sustainment portal | Strict | High |

Two consumers validate strictly. An additive field is therefore **not**
automatically non-breaking.

## Endpoints

### `GET /platforms`

Returns an array of platform records. `200 OK`.

### `GET /platforms/{platform_id}`

Returns a single platform record. `200 OK`, or `404 Not Found` with
`{"detail": "Platform not found"}`.

## Platform record

| Field | Type | Nullable | Description |
|---|---|---|---|
| `platformId` | string | No | Fleet-unique platform identifier |
| `designation` | string | No | Human-readable platform designation |
| `platformType` | string | No | `LAND`, `AIR` or `MISSION_SYSTEM` |
| `operational` | boolean | No | Platform-level operational flag |
| `subsystems` | array | No | Subsystem records, order significant |

No other fields are permitted at rev C.

## Subsystem record

| Field | Type | Nullable | Description |
|---|---|---|---|
| `subsystemId` | string | No | Platform-unique subsystem identifier |
| `name` | string | No | Subsystem name |
| `temperatureCelsius` | number | **Yes** | Most recent reading; `null` when unavailable |
| `operational` | boolean | No | Subsystem-level operational flag |

## Excluded from the interface

The following internal state is held by the service and **must not** be
exposed:

- `mission_critical_fault` — internal fault indication
- `telemetry_age_seconds` — internal telemetry staleness
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
  ]
}
```

## Conformance

`tests/contract/test_icd_phm_002_compatibility.py` asserts the rev C field set
exactly, on both endpoints. It runs as a separately named CI step
(`ICD contract tests`) so an interface violation is visibly distinct from an
ordinary test failure.

This test must never be weakened or deleted to make a change pass. A failure is
an interface-change escalation, not a test defect.

## Open interface changes

| Requirement | Proposed change | Status |
|---|---|---|
| SYS-4412 | Add derived `readinessState` to the platform record | Not implemented — requires rev D and consumer impact assessment |
