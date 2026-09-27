# Figueira factory — fresh run r03

## Team and authority

| Seat | Harness/model from supplied mandate | Responsibility |
|---|---|---|
| Figueira Planner | Codex / gpt-6-astra | Complete-requirement reading, decomposition, specification decisions, handoffs, acceptance/evidence reconciliation and final local report |
| Figueira Builder | Codex / gpt-6-astra | Product implementation, focused checks, source commits and verified repairs |
| Figueira Reviewer | Codex / gpt-6-astra | Independent specification-derived scenarios, official isolated checks, API/browser verification and explicit acceptance/rejection at full revision |

The three distinct configured seats were verified as members of room `769c0fe4-0d50-4507-9c8a-1ed742e1c477` before the first handoff. The human issued one autonomous dispatch for all four stages. There are no human clarification, approval or debugging gates in the assigned run. Exact generic mandates are in `mandates/`; product requirements belong in the task and handoffs, not those files.

## Reproducing the factory

1. Configure three distinct Band agent identities with the supplied seat mandates and the listed harness/model, and bind all three to one fresh room.
2. Prepare an empty result repository, a separate evidence directory, the read-only official requirements checkout, and permission to use existing Git, Docker and isolated headless browser tools without interactive permission prompts.
3. Give Planner the complete task, exact paths and authoritative requirements. Planner verifies membership and source identity, and publishes a durable room plan.
4. Reviewer derives acceptance scenarios from the complete requirements before reading implementation. Builder receives the complete relevant specification in the room, owns implementation files and commits, and returns exact revisions and evidence.
5. Reviewer independently tests the handed-off full revision, records reproducible expected/actual failures, and explicitly accepts or rejects. Verified defects go back to Builder with the complete applicable requirements; original failures and repair commits remain intact.
6. Freeze each accepted stage, copy it forward and widen only the new folder. Run cumulative checks and migration scenarios. At the end run all folders in the official isolated harness against a fresh local clone, reconcile evidence and report the exact local state.
7. The operator exports the authentic whole room after completion, prepares media and handles any later publication/submission. The factory never manufactures collaboration logs.

## Design choices and costs

This run uses sequential stage gates and separate implementation/review ownership. Complete specification handoffs cost additional context and wall time, but make the delegated contract inspectable. Pre-implementation acceptance derivation helps avoid treating visible samples as the full specification. The Planner's traceability map and Reviewer's scenario families are plans, not executed-test claims.

The initial API candidate uses Python standard-library modules, a threaded HTTP adapter and one transactional in-memory store. A single lock serializes state decisions; detached snapshots and immutable receipts separate current records from retry results. This favors auditable atomicity over multiple-worker throughput. State is intentionally ephemeral, as permitted by the specification. No runtime external services or assets are required by this design; container checks must verify the actual result.

Recorded run start: `2026-09-27T05:17:59Z`. Individual command timing is stored with execution evidence. Final elapsed time and actual suite counts will be stated in the terminal run report. Provider token usage and monetary/model spend are not available as verified measurements; no estimate is presented as measured spend. There were no authorized purchases or paid infrastructure activations.

## Failure handling and evidence integrity

Each official execution uses a fresh output directory. We preserve the command, timestamps, exit code, logs and report, including startup errors and failed reproductions. A missing response is not acceptance: the first Builder delegation exceeded the runtime's 10-minute reply window; the instruction was not resent, and local implementation commits were observed afterward. Product acceptance still requires the independent review outcome.

The first recorded stage-1 isolated attempt failed before tests because Docker BuildKit could not read an AppleDouble file's extended attributes on the mounted result filesystem. That is a startup/build-context failure, not a passed suite or a product assertion failure. Its original report and startup log are retained under `agent-evidence/builder/official-01/`.

The final report must distinguish distinct cases from repeated/cumulative executions, required suites from expected next-stage probes, and preparation from product acceptance. Known specification defects prevent independent acceptance even if sample checks pass. No conflict is manufactured for presentation.

Stage 1 demonstrates this distinction: the original review passed all 120 shipped cases but rejected four independently reproduced numeric/receipt/export failures. Builder had already produced exact-number and integer-range repairs in parallel when that rejection arrived. Reviewer then rechecked the original reproductions without weakening them and accepted the later exact revision with 86 independent cases passing. This is an independent rejection and verified repair, not a claim that a later review message caused an earlier implementation commit.

Stage 2 also passed all 145 required shipped checks but failed independent browser checks: a valid party size above JavaScript's exact integer range was rounded in single booking, pair booking and lookup. A separate caption-color correction improved a measured 4.4826:1 ratio to 5.3152:1; that visual observation was not the reason for rejection and its repair did not fix the functional failures. Both rejected revisions and the full raw-wire browser evidence are preserved. A distinct functional repair was assigned before permitting stage 3.

Mounted-volume metadata is not product source. Evidence-local Docker transport archives include only Git-tracked files and record file hashes; the final coordinator transport additionally compares each file with its exact committed blob before sending it to the installed Docker CLI. This avoids the observed AppleDouble/xattr build failure without patching official tests, product source or global configuration. Isolated browser checks use a fixed-destination local relay where internal Docker networking prevents direct host access, with no external browser origins or shared product volumes.

## Local boundaries

Official checkout and tests are read-only; previous submissions, old reports and historical rooms are excluded. Writable paths are the fresh result repository and the assigned fresh evidence root only. Installed runtime caches are tools, not product-source inputs. Synthetic fixtures are used for API/browser checks; the user's browser profile is never used. No global configuration change, external inference, publication or platform submission is part of this run.

Passwords and session-bearing export payloads are private test data. Evidence should record semantic comparisons and digests rather than exposing live credentials. The absent operator export means the offline package checker cannot yet verify the final room roster and reciprocal messages; that limitation must remain visible.
