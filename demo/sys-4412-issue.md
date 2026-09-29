## Requirement ID
SYS-4412

## Parent requirement
SYS-4400 — Fleet Availability Reporting

## Affected interface control document
ICD-PHM-002 rev C — Sustainment API external interface

## Criticality classification
Decision-support / advisory

## Requirement statement
The Platform Health service shall expose a `readinessState` field for every
monitored platform, with permitted values FMC, PMC and NMC, derived from
subsystem telemetry using a single authoritative classification rule.

## Source analysis (Microsoft 365 Copilot)

Synthesised from the fleet availability working group pack, ICD-PHM-002 rev C,
the sustainment operational concept and the open risk log.

**Driver.** Four downstream consumers — maintenance planning, sortie generation,
availability reporting and the customer sustainment portal — each implement
their own interpretation of platform usability from raw telemetry. Divergent
readiness figures have been reported between availability reporting and
maintenance planning for the same platform on the same date.

**Interface dependencies.** ICD-PHM-002 rev C is consumed by all four systems.
At least one consumer validates the response schema strictly. An additive field
is therefore not automatically non-breaking and requires consumer impact
assessment.

**Operational risk.** The dominant failure mode is optimistic misclassification.
A platform reported ready when it is not may be tasked. Missing or stale
telemetry must never be interpreted favourably.

**Compliance considerations.** Readiness figures feed contracted availability
reporting. The derivation rule must be documented, versioned and traceable to
this requirement, and the resulting evidence must be auditable.

## Acceptance criteria

1. `readinessState` present on both list and detail endpoints.
2. Permitted values exactly FMC, PMC, NMC.
3. Precedence rules applied deterministically and documented.
4. Boundary behaviour verified at 69.9, 70.0, 89.9 and 90.0 °C.
5. Missing, stale, malformed or non-finite telemetry never yields FMC.
6. All existing ICD-PHM-002 fields preserved unchanged.
7. Interface change assessed; ICD revised if the payload shape changes.
8. Unit, integration and contract tests pass without modification to existing
   assertions.
9. Requirement-to-test traceability recorded.
10. Residual risks recorded and accepted by a named engineering authority.

## Risks identified during analysis

- Optimistic classification on degraded or absent telemetry.
- Strict-schema consumers breaking on an additive field.
- Fault detail leaking through the public API.
- Readiness derivation diverging from the contracted availability definition.

## Required engineering gates
- [ ] Implementation plan approved by a human engineer
- [ ] Independent verification complete
- [ ] Safety and security review complete
- [ ] Interface change assessed and ICD revised if required
- [ ] Traceability matrix updated
- [ ] Residual risk accepted by named engineering authority
