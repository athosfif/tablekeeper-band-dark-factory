# Factory design

Three existing BAND identities cooperate in room `b11e30b4-d1a2-4a83-ba35-e97ca6bfc9e3`: `athoss.felipe/figueira-planner`, `athoss.felipe/figueira-builder`, and `athoss.felipe/figueira-reviewer`. Each is configured with Codex and `gpt-6-astra`. Their original generic mandates are preserved unchanged.

The standing mandates remain product-independent. Product requirements arrive in the room task. The reviewer is not the implementer. Handoffs must include the complete requirements and a committed revision. Agents coordinate repairs themselves. A failed run or blocker is preserved, never relabeled successful.

## Standing up the factory

1. Configure three distinct Band seats with the corresponding mandate files. Each mandate names the actual runtime and model. Requirements belong in the dispatched task rather than the mandates.
2. Give all seats explicit absolute paths for a read-only source specification, a separate output repository and a writable evidence directory. Make the required local build/test tools available before the autonomous run, keeping credentials outside the repository.
3. Dispatch one complete stage task to the Planner. The Planner reads the entire specification and guide, verifies the source revision, publishes an acceptance map and room-plan snapshot, and creates separate implementation and independent-review assignments.
4. The Builder implements and runs focused checks, then freezes a full committed revision. Every addressed handoff carries the complete task and applicable specification, including deployment limits. The Reviewer independently derives cases before reading implementation, then verifies the frozen revision with both the supplied harness and additional cases.
5. Genuine defects return with expected/actual behavior and reproducible evidence. Only the Builder edits service source. Repairs are new commits, followed by independent rechecks. The Planner assesses the evidence and reports the scoped outcome. No human clarification, approval or debugging instruction is needed during the assigned stage.

Private task lists track each seat's own work; the shared room board tracks cross-seat assignments. The active Markdown room plan is an immutable snapshot of `plan.md`. Source writes stop during exact-revision review. Documentation-only delivery commits preserve the tested stage tree and receive a separate packaging check.

## Implementation choices in the Stage 1 run

The Builder chose Python's standard library, the image's IANA timezone database and in-memory state under one process lock. This keeps the service in one offline-capable container. It trades horizontal scaling and restart persistence for an inspectable solution to the bounded single-container contract; persistence was explicitly optional.

Review exposed why locking alone was insufficient: an exception after a mutation could leave state partially committed. The repaired implementation prepares detached candidate state and encodes the response before publication, restoring the old state on exceptions. Iterative JSON handling preserves deeply nested retry bodies without Python call-stack failures. This adds state-copying work; measured container checks, including 50 in-flight requests, remained within the required response limits.

Full-spec messages cost more reading than links, but let each seat work from the same contract. Independent review was kept separate from implementation and materially changed the result. Bounded messaging timeouts were recorded as missing replies, not as a passing result or proof that a seat was unavailable. Existing assignments were not automatically resent.

## Actual failure recovery

| Evidence | What happened and how the factory responded |
|---|---|
| `builder-containers-01`, commits `c427c3b` → `f95a5cb` | Non-root startup failed because copied source permissions were owner-only. Builder added explicit Docker COPY permissions in a new commit; the original failed run remains. |
| `reviewer-rejection-01`, commit `f95a5cb` → `bea7a7` | Reviewer reproduced rejected creates/moves that still changed state, ordinary fixture fields with wrong error codes, and an unstated global table-ID uniqueness rule. The official run was 114/120; the threshold-based stage claim was not accepted as completion. Builder repaired transaction publication, JSON handling, type distinctions and restaurant/table scoping. |
| `reviewer-rejection-02`, commit `bea7a7` → `0f96bf0` | The official 120/120 pass still left an independently reproduced opaque-ID routing defect. Builder fixed route recognition before single decoding. The complete final independent and official checks then passed. |
| Reviewer run setup and oracle logs | An internal-network client setup failed, a Docker tar transport attempt failed, and a reviewer assertion incorrectly required a DST slot to end exactly at closing. The reviewer corrected its own tooling/oracle and preserved the original failures without attributing them to the service. |

Planner supplied two concrete black-box candidates; Reviewer independently reproduced them against frozen commits. Reviewer also found its own validation and table-scope defects. The room's handoffs, test artifacts and original Git history demonstrate the division of work; this narrative does not substitute for them. No disagreement was manufactured and no history was amended, rebased or squashed.

## Results, time and cost

Final API revision: `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`. The [stage report](STAGE-1-REPORT.md) contains the evidence index and limits.

- Builder: 21 focused groups passed on the final API revision; 551 instrumented HTTP requests plus two in-memory raw exports. One group is local fault injection, while service HTTP groups use two constrained Docker containers.
- Reviewer: 27 independent groups passed, 955 requests, zero observed 5xx, 13.082 seconds test time. Maximum ordinary request 3.351785 seconds; maximum test-control call 0.121121 seconds.
- Supplied official harness: isolated Stage 1 120/120, no failures/errors/skips/deselections, 20.94 seconds suite time. The expected next-stage probe stopped at the absent UI.
- The first observed coordinator room check was 2026-09-26 16:22:44 UTC. The final official run finished at 17:13:56.902652 UTC: an observed interval of about 51 minutes 13 seconds, including implementation, review, repairs, image preparation and messaging delays. Final report/packaging work follows that measured checkpoint.

Per-seat token usage and monetary spend were not available from the evidence collected, so no estimate is invented. The existing configured runtimes were used; no new paid infrastructure or provider was activated.

## Evidence boundaries

All run artifacts are under `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`. New directories preserve every attempt, including test-source copies, commands, timings and revision checks. Test identities are synthetic. Tokens and state exports remain in test-process memory, not committed files.

The original source checkout remains read-only. A recorded, process-local Docker transport adapter was needed for pre-existing macOS AppleDouble metadata; it streams unchanged ordinary harness files and excludes metadata/caches, without modifying official tests or global configuration. A standard clean source checkout does not need that volume-specific workaround.

Only Stage 1 was assigned. No later stage, public repository publication, room export, presentation/video submission or official event acceptance is claimed. Hidden checks remain unavailable; finite local tests and source inspection are the evidence for this stage outcome.
