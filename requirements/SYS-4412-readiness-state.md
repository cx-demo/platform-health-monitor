# Requirement SYS-4412 — Derived platform readiness state

| Field | Value |
|---|---|
| Requirement ID | SYS-4412 |
| Parent requirement | SYS-4400 — Fleet Availability Reporting |
| Affected ICD | ICD-PHM-002 rev C — Sustainment API external interface |
| Criticality classification | Decision-support / advisory |
| Status | Raised — not implemented |

> **Classification note.** This is decision-support. It is **not**
> flight-critical and **not** safety-of-life. The classification is recorded so
> the control set applied is visibly proportionate. Nothing here claims
> DO-178C, DEF STAN 00-055 or IEC 61508 certification credit.

## Requirement statement

> The Platform Health service shall expose a `readinessState` field for every
> monitored platform. Permitted values shall be `FMC`, `PMC` and `NMC`, derived
> from subsystem telemetry using a single authoritative classification rule.

## Background

The sustainment API currently exposes raw subsystem telemetry only. Four
downstream consumers — maintenance planning, sortie generation, availability
reporting and the customer sustainment portal — each re-implement their own
interpretation of whether a platform is usable. Divergent readiness figures
have been reported for the same platform on the same date.

## Classification rules

Evaluated in precedence order. The first matching condition determines the
state.

| Precedence | Condition | `readinessState` |
|---|---|---|
| 1 | Any subsystem reports a mission-critical fault | `NMC` |
| 2 | Any subsystem temperature at or above 90 °C | `NMC` |
| 3 | Platform not operational | `NMC` |
| 4 | Any subsystem temperature 70 °C to below 90 °C | `PMC` |
| 5 | Any subsystem degraded but mission-capable | `PMC` |
| 6 | Telemetry missing, stale or non-finite for any subsystem | `PMC` with `readinessConfidence: LOW` |
| 7 | All subsystems nominal and operational | `FMC` |

> Thresholds are synthetic for this service baseline. The engineering value is
> in having **one** versioned, traceable derivation rule — not in the specific
> numbers.

The safety-relevant rule is rule 6: **missing telemetry must never silently
produce `FMC`**. In every consuming domain, a false "ready" is the dangerous
failure mode.

## Non-functional requirements

- Preserve every existing API field — ICD-PHM-002 consumers must not break.
- Additive schema change only; version the contract.
- Unit tests at every threshold boundary; integration tests on both endpoints.
- Safe handling of missing, stale, malformed and non-finite telemetry.
- Never report `FMC` on incomplete data.
- No internal diagnostic detail or fault codes leaked through the public API.
- Full requirement-to-test traceability.
- Residual risk recorded and accepted by a named engineering authority.

## Acceptance criteria

1. `readinessState` present on both list and detail endpoints.
2. Permitted values exactly `FMC`, `PMC`, `NMC`.
3. Precedence rules applied deterministically and documented.
4. Boundary behaviour verified at 69.9, 70.0, 89.9 and 90.0 °C.
5. Missing, stale, malformed or non-finite telemetry never yields `FMC`.
6. All existing ICD-PHM-002 fields preserved unchanged.
7. Interface change assessed; ICD revised if the payload shape changes.
8. Unit, integration and contract tests pass without modification to existing
   assertions.
9. Requirement-to-test traceability recorded.
10. Residual risks recorded and accepted by a named engineering authority.

## Interface impact

Adding `readinessState` changes the ICD-PHM-002 platform record. Two consumers
validate the response schema strictly, so this is **not** automatically a
non-breaking change. It requires:

- a revision of `docs/icd/ICD-PHM-002.md` to rev D,
- a recorded consumer impact assessment,
- Interface Control Board review (enforced via `.github/CODEOWNERS`).

The contract suite in `tests/contract/` will fail until the interface change is
properly assessed and the declared field set revised. That failure is the
intended control. It must not be resolved by weakening the test.

## Identified risks

- Optimistic classification on degraded or absent telemetry (see RSK-4).
- Strict-schema consumers breaking on an additive field (see RSK-3).
- Fault detail leaking through the public API (see RSK-2).
- Readiness derivation diverging from the contracted availability definition.
