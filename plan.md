# Tablekeeper fresh factory run r03

This run is authorized by the single dispatch in room `769c0fe4-0d50-4507-9c8a-1ed742e1c477`. Authoritative requirements are the complete participant guide and Tablekeeper specifications at upstream commit `803560d2a678ace1414465c098eb0ab5380ffade`. No historical implementation or room evidence is input.

## Ownership and sequence

Current gate: stage 1 accepted at `ec96785a3aaa611e8519d09869cade8ffddb9224`, frozen tree `dfff49710165dc7d568496f1d230b4fc69eb7b2c`. Stage 2 accepted at `e44838741cc906fbcae88e4248b5dc850af90e7c`, frozen tree `b33e79f9bb65ff730b626f9c774afa4653b11e59`. Stage 3 accepted at `6b75841c243ea4722be08834526545ea847bad27`, frozen tree `3c21f70a1e2d2f2a615c1e1b4a3ab50d2bb699fb`. Stage 4 accepted at `bb417f29a586fe0771fcc728ab308584f00d5b9a`, frozen tree `2473ec5b52d8ab4ea53e6ce5f75eeb358f2bd719`. All source gates are complete and original failures remain evidence. The final package gate uses the committed documentation and a fresh exact clone; its observed outcome is recorded outside the repository at the authorized evidence root in `agent-evidence/coordinator/final-report.md`, `final-manifest.json` and `final-package-01/official/summary.json`.

Planner owns decomposition, requirement decisions, evidence reconciliation and the final report. Builder owns all product implementation and implementation commits. Reviewer derives acceptance cases before implementation inspection and independently accepts or rejects exact commits. Only one seat writes a given file; review artifacts live under the assigned agent-evidence root.

1. Build stage 1 as a standalone JSON API. Review atomicity, errors, authorization, time/DST, replay receipts and state portability; run isolated official checks. Repair verified failures before acceptance.
2. Freeze stage 1. Copy to stage 2 and add combined tables and the English browser product, including stale-search and uncertain-booking recovery. Review independent API and real browser journeys and stage-1 migration.
3. Freeze stage 2. Copy to stage 3 and add policy selection, accepted terms, immutable history, optimistic revisions and recurring agreements. Review migration from stages 1 and 2 and concurrent collective operations.
4. Freeze stage 3. Copy to stage 4 and add deterministic closure replanning and atomic recurring amendments. Review objective ordering, stale plans, closures, exceptions, preservation and all prior migrations.
5. Run the official all-folder isolated harness against a fresh local clone with unique output directories. Reconcile every acceptance with full commit and tree identifiers; record limitations and the absent operator-supplied room export.

## Acceptance map

| Requirement group | Required evidence |
|---|---|
| Stage 1 sections 2–6: container, reset, errors, auth | Clean single-image startup with PORT, offline limits; malformed/type/range checks; privacy, token and password-hash behavior |
| Stage 1 sections 7–11: bookings, time, state, moves | Same-key/different-key races, occupancy and rollback, DST gaps/folds and absolute duration, immutable replay after mutation, replacement imports and atomic swaps |
| Stage 2: cumulative API and pairs | Every declared pair and no transitive combinations; complete occupancy, canonical ordering, move rollback and cumulative checks |
| Stage 2: product and recovery | 375px/desktop screenshots, labels/focus/keyboard, stale searches, lost committed response retry, conflicting booking with preserved input, identity under navigation/selection changes |
| Stage 3: policies/history | Publication/effective-date ordering, ties, permission errors, accepted-term cutoff, no-op versus real mutation, revision races, immutable receipts/history and migration |
| Stage 3: series/moves | Anchor preserved, calendar recurrence/DST, atomic failure, permanent exceptions, cancellation independence, per-operation counters |
| Stage 4: plans | Independent deterministic objective checks; preview read-only; fixed-booking/closure constraints; accepted capacity; stale/apply/replay races; no partial changes |
| Stage 4: series amendments | Original scheduled dates, exception/cancel exclusion, no-op handling, error precedence, expected-revision races and all-or-nothing preservation |
| Final package | All four independent stage trees, exact mandate-byte hashes, preserved history, official isolated reports and honest missing-room-export result |

Passing shipped checks is directional evidence, never proof of hidden-check correctness. Counts distinguish distinct test cases from cumulative executions. Expected next-stage probe failures are separate from required checks. No source, mandates or tests are imported from earlier runs. No publication, submission, paid service, external inference or fabricated room export is authorized.

The coordinator stops after the final local package report. Authentic whole-room export, media, public verification and submission remain operator work after completion. Missing `room.json` must remain an explicit offline-check limitation, never a fabricated pass.
