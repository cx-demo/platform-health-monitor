# platform-health-monitor

**Platform Health & Mission Readiness Service (PHMS)**

A sustainment API for a mixed fleet. Each platform — a land vehicle, an air
platform, a deployed mission system — reports subsystem telemetry to a common
interface. Maintenance planning, sortie generation and availability reporting
all consume it.

This repository is a demonstration baseline for governed, evidenced engineering
change: requirement → plan → implementation → independent verification →
safety and security assurance → traceable evidence → pull request → enforced
governance gate → named human approval.

## Scenario

At ICD-PHM-002 rev C the API exposed **raw subsystem telemetry only**. Every
downstream consumer re-implemented its own interpretation of "is this platform
usable", and they disagreed. `SYS-4412` adds a single authoritative
`readinessState` derivation (`FMC` / `PMC` / `NMC`) plus `readinessConfidence`
(`HIGH` / `LOW`), under rule `SYS-4412-R1` and draft ICD rev D. Rev D is served
on a parallel `/v2` surface (PHMS 2.4.0); `/platforms` stays at rev C with no
readiness fields, and consumers opt in by base path. See
`demo/sys-4412-issue.md` for the engineering change request.

## Fleet fixture

| Platform | Type | Notes |
|---|---|---|
| `LND-114` | `LAND` | Nominal |
| `AIR-207` | `AIR` | Gearbox running warm (78 °C) |
| `MSN-330` | `MISSION_SYSTEM` | Mission-critical fault, 94 °C generator, stale comms telemetry |

None of that condition is visible through the rev C `/platforms` API. The
rev D `/v2/platforms` API publishes the derived readiness (`FMC`, `PMC`, `NMC`
respectively); the fault and telemetry age stay internal.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --reload
```

- `GET http://127.0.0.1:8000/platforms` — rev C, no readiness
- `GET http://127.0.0.1:8000/platforms/LND-114` — rev C
- `GET http://127.0.0.1:8000/v2/platforms` — rev D, with `readinessState` and `readinessConfidence`
- `GET http://127.0.0.1:8000/v2/platforms/LND-114` — rev D
- `http://127.0.0.1:8000/docs` · `/v2/docs` — Swagger UI, interactive
- `http://127.0.0.1:8000/redoc` · `/v2/redoc` — ReDoc, reads better as an interface spec
- `GET http://127.0.0.1:8000/openapi.json` (2.3.0, rev C) · `/v2/openapi.json` (2.4.0, rev D) — machine-readable forms of the ICD

### Fleet plate

- `GET http://127.0.0.1:8000/dashboard` — a read-only visualisation of the fleet

The plate is a browser-side consumer of `GET /v2/platforms`, not an extension of
the interface. It holds no privileged access and reads the same payload any
integrator receives, so whatever it cannot show you, no consumer can show you.
It is deliberately excluded from `/openapi.json` and `/v2/openapi.json`: those are the
machine-readable forms of ICD-PHM-002, and adding a path to either would be an
interface change.

## Test it

```bash
pytest tests/unit
pytest tests/integration
pytest tests/contract          # ICD-PHM-002 conformance
pytest --cov=src --cov-report=term --cov-fail-under=90
```

All four run in CI under the check context
`Unit, integration and contract tests`.

## Interface control

`docs/icd/ICD-PHM-002.md` is a **controlled interface document**. Rev C is
baselined for `/platforms`; rev D (SYS-4412, `/v2`) is drafted and awaits
Interface Control Board approval.
`tests/contract/test_icd_phm_002_compatibility.py` asserts the rev C field set
exactly on both `/platforms` endpoints and is unchanged.
`tests/contract/test_icd_phm_002_rev_d.py` asserts the rev D field set exactly
on both `/v2` endpoints and checks it against the ICD rev D platform record
table so the two cannot drift.

Two downstream consumers validate the response schema strictly, so an additive
field is **not** automatically non-breaking. A payload change therefore needs an
ICD revision, and `tests/contract/` is updated to the new revision in the same
pull request, at least as strictly. The controls:

- weakening, skipping or deleting contract tests to make a change pass is
  forbidden by `.github/copilot-instructions.md`; a contract failure on an
  unrevised ICD is an interface-change escalation, not a test defect,
- `tests/contract/` and `docs/icd/` are CODEOWNER-protected by the interface
  control board, whose approval of both is required,
- the contract suite is a required status check.

The correct resolution is an ICD revision to rev D plus a recorded consumer
impact assessment.

## Layout

```text
.github/
  copilot-instructions.md          repository engineering rules for Copilot
  CODEOWNERS                       engineering authority / interface control board
  dependabot.yml
  ISSUE_TEMPLATE/engineering-change.yml
  rulesets/main-protection.json    branch protection, applied by an admin
  workflows/                       ci · codeql · dependency-review
demo/sys-4412-issue.md             body for the SYS-4412 engineering change issue
docs/
  architecture.md
  icd/ICD-PHM-002.md               controlled interface document (rev D draft)
src/                               models · repository · readiness_service · main
tests/                             unit · integration · contract
```

## Governance layer

| Control | Mechanism |
|---|---|
| Test, contract and 90% coverage gate | `.github/workflows/ci.yml` |
| Static security analysis | `.github/workflows/codeql.yml` (`security-extended`) |
| Supply chain | `.github/workflows/dependency-review.yml`, `dependabot.yml` |
| Branch protection | `.github/rulesets/main-protection.json` |
| Ownership | `.github/CODEOWNERS` |

Requirement IDs, requirement-to-test coverage, risks, decisions and evidence
links belong in the issue or pull request and are assessed during human review.
There is no automated requirement-ID check.
CI uploads test results as the `test-evidence` artifact.

The ruleset sets `require_last_push_approval: true` — **an agent cannot push a
change and have it count as approved.**

## Cross-session evidence convention

Sessions run in isolated worktrees. Shared records must not depend on access to
another session's chat:

1. Every review session records findings, decisions, agent context summaries
   and evidence links in the issue or pull request.
2. Review sessions branch from the **pushed** implementation branch.
3. Consolidation reads the issue or pull request, linked check results and
   `git diff`, not private session transcripts.

## Repository administrator setup

These steps require org/admin scope and are **not** applied by this repository's
contents alone.

The versioned ruleset now requires only the test, CodeQL and dependency-review
checks. An administrator must synchronize any existing GitHub ruleset before
merging the workflow removal; otherwise the deleted check can still block merge.
Live ruleset synchronization for this change is unverified.

> ### Current state
>
> The repository is **public**, so code scanning and dependency review are
> available at no cost. Already configured and verified green:
>
> | Feature | State |
> |---|---|
> | Code scanning (CodeQL, advanced setup) | Enabled |
> | CodeQL default setup | **Disabled — required** |
> | Secret scanning + push protection | Enabled |
> | Dependency graph + Dependabot security updates | Enabled |
>
> **CodeQL default setup must stay off.** With it enabled, the SARIF from
> `.github/workflows/codeql.yml` is rejected with *"CodeQL analyses from
> advanced configurations cannot be processed when the default setup is
> enabled"*. Keeping the workflow authoritative means the query suite is
> versioned and reviewable rather than a UI toggle:
>
> ```bash
> gh api -X PATCH /repos/$REPO/code-scanning/default-setup -f state=not-configured
> ```
>
> If the repository is ever made private again, code scanning and dependency
> review require a purchased GHAS licence. Do **not** resolve that by deleting
> the workflows or dropping them from the ruleset — lowering a gate you cannot
> satisfy is the exact behaviour this repository exists to argue against.

```bash
REPO=<org>/platform-health-monitor

# 1. Security features (public repository; GHAS licence needed if private)
gh api -X PATCH /repos/$REPO \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled' \
  -f 'security_and_analysis[dependabot_security_updates][status]=enabled'

gh api -X PATCH /repos/$REPO/code-scanning/default-setup -f state=not-configured

# 2. Apply branch protection — do this AFTER the baseline PR has merged,
#    otherwise the ruleset blocks the very pull request that introduces it
gh api -X POST /repos/$REPO/rulesets \
  --input .github/rulesets/main-protection.json

# 3. Create the engineering change record
gh issue create --repo $REPO \
  --title "[SYS-4412] Expose derived platform readiness state on sustainment API" \
  --body-file demo/sys-4412-issue.md \
  --label engineering-change,requires-plan-approval
```

Checklist:

- [x] Repository public; code scanning, secret scanning, push protection,
      dependency graph and Dependabot enabled
- [x] CodeQL default setup disabled so the committed workflow is authoritative
- [x] CodeQL has completed a successful run (required checks need history)
- [x] `@cx-demo` confirmed as a collaborator with admin access (engineering
      authority — owns `src/`, `.github/workflows/`, `.github/rulesets/`)
- [x] `@pedric1` confirmed as a collaborator with write access (interface
      control board — owns `docs/icd/` and `tests/contract/`)
- [x] `CODEOWNERS` resolves cleanly — `gh api /repos/$REPO/codeowners/errors`
      returns no errors. GitHub silently ignores entries it cannot resolve,
      leaving those paths unprotected, so verify this rather than assume it
- [x] All four required checks green on the baseline pull request
- [x] Baseline pull request merged to `main`
- [ ] Live `main-engineering-governance` ruleset synchronized with the updated
      `.github/rulesets/main-protection.json`
- [x] `require_last_push_approval` confirmed on — the implementing engineer
      cannot self-approve an interface change
- [x] **Verified a direct push to `main` is actually refused** —
      `! [remote rejected] HEAD -> main (push declined due to repository rule
      violations)`. Tested, not assumed.
- [x] SYS-4412 engineering change issue created with gate checkboxes unticked
- [ ] SYS-4412 issue created with gate checkboxes unticked

## Scope note

This repository produces the evidence artifacts that assurance processes
consume. It does **not** claim DO-178C, DEF STAN 00-055 or IEC 61508
certification credit. `SYS-4412` is classified decision-support / advisory, and
the control set is proportionate to that classification.
