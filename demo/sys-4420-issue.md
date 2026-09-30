# Requirement ID

SYS-4420 — **Proposed; not approved for implementation**

# Parent requirement

SYS-4400

# Affected interface control document

ICD-PHM-002. Current repository state: rev C is baselined for `/platforms`;
rev D is a draft for the parallel `/v2` surface and awaits Interface Control
Board approval.

SYS-4420 is a requirement proposal only. It does not revise the ICD or approve
an API change. Any public payload change proposed to satisfy this requirement
must undergo a controlled ICD revision and strict-consumer impact assessment
before implementation.

# Criticality classification

Decision-support / advisory

# Requirement statement

The Platform Health & Mission Readiness Service shall provide coordinators with
advisory telemetry freshness and coverage information that identifies when
published subsystem telemetry was observed, distinguishes stale telemetry from
telemetry whose freshness is unknown, and does not represent retrieval,
publication, or response-generation time as observation time.

Freshness and coverage information shall not determine or modify readiness
state, readiness confidence, maintenance tasking, sortie tasking, or other
operational decisions. The requirement shall not introduce unapproved
freshness limits, clock-skew tolerances, coverage thresholds, retention periods,
or access decisions.

# Source analysis (Microsoft 365 Copilot)

Coordinators currently cannot tell from a published subsystem value when its
underlying observation occurred. Retrieval time can be mistaken for observation
time, making old evidence appear current. Missing timestamp provenance also
prevents consumers from reliably separating stale evidence from evidence whose
freshness cannot be established.

The proposed capability is advisory reporting. Human authorities must define
timestamp provenance, freshness policy, policy ownership, clock-skew handling,
access, retention, and acceptable performance before implementation. No
threshold or operational limit was approved during analysis.

ICD-PHM-002 currently identifies rev C as baselined for `/platforms` and rev D
as a draft for `/v2`. Both maintenance planning and the customer sustainment
portal validate schemas strictly. Therefore, even additive public fields may be
breaking changes. Any proposed public payload must be handled through a
controlled ICD revision, exact-field contract updates, and a strict-consumer
migration and rollback assessment.

Human decisions required before implementation:

- What source event establishes observation time, and which system is
  authoritative for timestamp provenance?
- Who owns and approves freshness policy, including any subsystem-specific
  limits and change-control process?
- How must missing, malformed, future-dated, or clock-skewed timestamps be
  represented without implying known freshness?
- What migration, compatibility, and rollback approach is acceptable for
  strict consumers?
- Who may access freshness history or coverage reporting, and what retention
  period is approved?
- What fleet size, subsystem count, query pattern, latency, and throughput
  envelope must be demonstrated?

# Acceptance criteria

1. A human-approved data definition identifies observation time, its source,
   its authoritative clock, and how it differs from ingestion, retrieval,
   publication, and response-generation times.
2. Proposed reporting distinguishes at least current-under-approved-policy,
   stale-under-approved-policy, and unknown freshness without substituting
   retrieval or response time for missing observation time.
3. Coverage reporting states its numerator, denominator, aggregation scope, and
   reporting window. No coverage target or pass/fail threshold is introduced
   without named human approval.
4. Missing, malformed, future-dated, and clock-skewed timestamps produce an
   explicit unknown or invalid advisory result according to approved policy;
   they never produce a more favourable freshness or coverage result.
5. Freshness and coverage outputs are demonstrably advisory and do not feed,
   override, or modify readiness classification, readiness confidence,
   maintenance tasking, sortie tasking, or other operational decision logic.
6. Any proposed public API payload change is preceded by a controlled
   ICD-PHM-002 revision and strict-consumer impact assessment covering schema
   adoption, compatibility, migration, rollback, and exact-field contract
   tests.
7. Access control and retention requirements for observation timestamps,
   freshness history, and coverage reports are approved by named human owners
   before implementation.
8. A human-approved fleet-size and performance envelope is defined, and
   verification demonstrates reporting within that envelope without inventing
   operational limits.
9. Requirement-to-test coverage, unresolved questions, material risks,
   evidence links, and named human acceptance decisions are recorded in the
   implementation issue or pull request before merge.

# Risks identified during analysis

- Ambiguous timestamp provenance could present ingestion or retrieval time as
  observation time and make stale evidence appear current.
- Unapproved freshness or coverage thresholds could become de facto operational
  limits without engineering authority.
- Missing, malformed, future-dated, or clock-skewed timestamps could be
  misclassified as fresh instead of unknown or invalid.
- Consumers could use advisory output for readiness or tasking despite the
  requirement boundary.
- Additive fields could break strict consumers if introduced without an ICD
  revision, migration plan, and exact-field contract changes.
- Timestamp history may expose sensitive operational patterns or exceed an
  approved retention purpose.
- Fleet-wide aggregation may create unacceptable latency, storage, or query
  load if scale and performance expectations remain undefined.
- Rev D is still draft; designing SYS-4420 against an assumed approved rev D
  baseline could create compatibility and governance errors.

**Status:** Proposed requirement record only. No implementation, API change,
ICD revision, operational threshold, or human approval is asserted.
