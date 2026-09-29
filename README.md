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

The API currently exposes **raw subsystem telemetry only**. Every downstream
consumer re-implements its own interpretation of "is this platform usable", and
they disagree. `SYS-4412` proposes a single authoritative `readinessState`
derivation (`FMC` / `PMC` / `NMC`).

`readinessState` is **deliberately not implemented here.** This repository is
the *before* state. See `requirements/SYS-4412-readiness-state.md`.

## Fleet fixture

| Platform | Type | Notes |
|---|---|---|
| `LND-114` | `LAND` | Nominal |
| `AIR-207` | `AIR` | Gearbox running warm (78 °C) |
| `MSN-330` | `MISSION_SYSTEM` | Mission-critical fault, 94 °C generator, stale comms telemetry |

None of that condition is visible through the current API. That is the problem.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.main:app --reload
```

- `GET http://127.0.0.1:8000/platforms`
- `GET http://127.0.0.1:8000/platforms/LND-114`
- `GET http://127.0.0.1:8000/openapi.json` — machine-readable form of the ICD

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

`docs/icd/ICD-PHM-002.md` is a **controlled interface document**, currently at
rev C. `tests/contract/test_icd_phm_002_compatibility.py` asserts the declared
field set exactly, on both endpoints.

Two downstream consumers validate the response schema strictly, so an additive
field is **not** automatically non-breaking. Adding `readinessState` will turn
the contract suite red. That is the intended control, not a defect:

- weakening or deleting the contract test is forbidden by
  `.github/copilot-instructions.md`,
- `tests/contract/` and `docs/icd/` are CODEOWNER-protected by the interface
  control board,
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
  workflows/                       ci · codeql · dependency-review · traceability
demo/sys-4412-issue.md             body for the SYS-4412 engineering change issue
docs/
  architecture.md
  icd/ICD-PHM-002.md               controlled interface document (rev C)
  evidence/                        cross-session evidence surface
  risk-register.md
  traceability-matrix.md
requirements/SYS-4412-readiness-state.md
src/                               models · repository · readiness_service · main
tests/                             unit · integration · contract
```

## Governance layer

| Control | Mechanism |
|---|---|
| Test, contract and 90% coverage gate | `.github/workflows/ci.yml` |
| Static security analysis | `.github/workflows/codeql.yml` (`security-extended`) |
| Supply chain | `.github/workflows/dependency-review.yml`, `dependabot.yml` |
| Requirement traceability | `.github/workflows/traceability.yml` |
| Branch protection | `.github/rulesets/main-protection.json` |
| Ownership | `.github/CODEOWNERS` |

`traceability.yml` is a bespoke gate: a pull request fails unless it carries a
`SYS-NNNN` requirement ID, updates `docs/traceability-matrix.md`, and leaves
evidence in `docs/evidence/`. Organisations do not merge on green tests alone;
they merge on evidence.

The ruleset sets `require_last_push_approval: true` — **an agent cannot push a
change and have it count as approved.**

## Cross-session evidence convention

Sessions run in isolated worktrees and cannot read each other's chat. Therefore:

1. Every review session **commits and pushes** its report to `docs/evidence/`.
2. Review sessions branch from the **pushed** implementation branch.
3. Consolidation reads committed files and `git diff`, never chat transcripts.

## Repository administrator setup

These steps require org/admin scope and are **not** applied by this repository's
contents alone.

> ### ⚠️ GHAS licence is a hard prerequisite
>
> This repository is **private** and GitHub Advanced Security has not been
> purchased for the organisation. Verified:
>
> ```
> PATCH /repos/<org>/platform-health-monitor
>   security_and_analysis[advanced_security][status]=enabled
> → 422 "Advanced security has not been purchased."
> ```
>
> Without GHAS, **`CodeQL analysis` and `Dependency Review` cannot pass** —
> CodeQL runs but its SARIF upload is rejected because code scanning is off,
> and dependency review is unsupported on a private repository. Two of the four
> required status checks are therefore permanently red.
>
> Fix it one of two ways before the demo:
>
> 1. Assign GHAS (Code Security + Secret Protection) to the repository, or
> 2. Make the repository **public**, where both are free.
>
> Do **not** resolve this by deleting the workflows or dropping them from the
> ruleset. Lowering a gate you cannot currently satisfy is the exact behaviour
> this repository exists to argue against.
>
> Already enabled and working: dependency graph, Dependabot security updates.

```bash
REPO=<org>/platform-health-monitor

# 1. Enable GHAS (requires a purchased licence, or a public repository)
gh api -X PATCH /repos/$REPO \
  -f 'security_and_analysis[advanced_security][status]=enabled' \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled' \
  -f 'security_and_analysis[dependabot_security_updates][status]=enabled'

# 2. Apply branch protection
gh api -X POST /repos/$REPO/rulesets \
  --input .github/rulesets/main-protection.json

# 3. Create the engineering change record
gh issue create --repo $REPO \
  --title "[SYS-4412] Expose derived platform readiness state on sustainment API" \
  --body-file demo/sys-4412-issue.md \
  --label engineering-change,requires-plan-approval
```

Checklist:

- [ ] **GHAS licensed, or repository made public** — blocks two required checks
- [ ] Code scanning enabled and CodeQL has completed at least one successful
      run (required checks need history)
- [ ] Secret scanning and push protection enabled
- [ ] **`@cxdemosg` added as a repository collaborator with write access** —
      this account does not currently exist as a GitHub user and is not a
      collaborator. GitHub **silently ignores** unresolvable `CODEOWNERS`
      entries, so `/src/`, `/.github/workflows/` and `/.github/rulesets/` are
      unprotected until this is fixed. Verify with
      `gh api /repos/$REPO/codeowners/errors`.
- [ ] `@pedric1` confirmed as a collaborator with write access (interface
      control board — owns `docs/icd/` and `tests/contract/`)
- [ ] Note: `require_last_push_approval` bars the last pusher from approving,
      so the implementing engineer cannot self-approve an interface change
- [ ] All four workflows present and green on `main`
- [ ] Ruleset applied and active
- [ ] `require_last_push_approval` confirmed on
- [ ] **Verified an administrator merge is actually blocked** — test it, do not
      assume
- [ ] SYS-4412 issue created with gate checkboxes unticked

## Scope note

This repository produces the evidence artifacts that assurance processes
consume. It does **not** claim DO-178C, DEF STAN 00-055 or IEC 61508
certification credit. `SYS-4412` is classified decision-support / advisory, and
the control set is proportionate to that classification.
