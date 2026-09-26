# Stage 2 result

Stage 2 is independently ready as a local factory outcome. It extends the accepted Stage 1 API with the English booking product, declared combined-table seating, stale-search/selection recovery and uncertain-response retries. This is not official judging, publication or submission.

## Revisions and preserved baseline

- Continuation baseline delivery: `e5c256641653de82a97222d1126308fbde6188f6`; accepted Stage 1 source `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`.
- Immutable Stage 1 tree: `0050accbdc6d0457ffdc73de6365158e65c1808b`.
- Stage 2 implementation: `61949b2abbb444a9ac082ee48c7109ef9423a3a2`.
- Independently accepted repair/source: `2e026c006569b2e749de79b7526f03ae9b6e44e3`.
- Accepted Stage 2 tree: `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8`.

The full service lives in `stage-2/`; [RUN.md](stage-2/RUN.md) builds it from that directory alone. Prior folders, generic mandates and all commits remain unchanged. Root documentation commits do not alter the accepted stage trees.

## Actual verification

All evidence below is under `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-2`.

| Run | Actual result |
|---|---|
| `reviewer-api-02` | 36/36 independent groups; 1,205 instrumented HTTP calls; zero failures/errors/5xx; 14.461s. Maximum ordinary request 2.551795710s, control 0.259250417s. |
| `reviewer-browser-03` | 10/10 independent Chromium groups; 21.669s; 46 instrumented setup/control calls plus additional browser traffic. No observed instrumented 5xx. |
| `reviewer-official-02/harness` | Isolated cumulative Stage 1: 120/120 in 20.03s; Stage 2: 25/25 in 20.61s. Zero failures/errors/skips/deselections; harness exit 0, 49.183s command. |
| Same official invocation, next-stage probe | Stage 3: 7 collected, 0 passed, 1 expected missing-policy-endpoint failure; 6 unexecuted under fail-fast, 0.23s. Not Stage 3 implementation. |
| `builder-run-04` | Builder reported 29 focused groups on frozen accepted source, 657 direct HTTP calls plus browser traffic, 18.297s unittest, maximum direct request 2.0729s. Separate from independent proof. |
| `planner-ui-01` → `planner-ui-02` | Exact-commit layout probe reproduced 594px scroll width at 375px, then verified 375/375 after the repair; ordinary name also 375/375. Own constrained container, ordinary published networking, not isolated acceptance. |

Reviewer API/browser services ran on internal Docker networks with blocked outbound probes, no service mounts, 2 CPU/2 GiB each, default 8080 and override 8097. Actual populated Stage 1 source and separate Stage 2 destination preserved accounts, multiple tokens, references and original create/batch receipts. A still-open signed-in form recovered its original Stage 1 booking response after export/import without reload. Tokens and state exports stayed in memory.

Final independent health observations were 0.550/0.488/0.476s (API mode) and 0.848/0.859/0.543s (browser mode) for source/destination/Stage 1. Separate RUN.md published-port smoke was 0.470s and 0.360s. Local fonts, scripts and styles loaded without external assets. Desktop and 375px rendered screenshots are in `reviewer-browser-03/`.

## Real review and repair

Planner's independent layout probe found a valid long restaurant name expanding the mobile page to 594px. Reviewer reproduced it at 588px on the exact clean initial commit and rejected Stage 2 even though the supplied cumulative tests passed 145/145. Builder repaired text wrapping and layout shrinkage in a new commit. Reviewer rechecked search, empty state, booking/confirmation and lookup with complete readable labels. Planner's original regression also passed on the accepted commit. No artificial input restriction or hidden clipping was introduced.

The independent acceptance design preceded source inspection. `reviewer-browser-01` preserves a reviewer login-helper synchronization error; it was corrected in test tooling and not attributed to the product. Later screenshot-marker extraction was repaired without modifying original logs. Source rejection is in `reviewer-rejection-01.md`; final explicit acceptance and complete limits are in `reviewer-final-report.md`. Builder handoff/repair reports and all failed runs remain intact.

Official isolation used a new evidence-local copy of the previously documented metadata-only Docker transport adapter. It preserves ordinary official source/tests and filters pre-existing AppleDouble context metadata. Original Stage 1 evidence and official input were not modified.

## Limits and next authorized stage

Finite tests cannot establish every interleaving or held-back test. Instrumented HTTP counts exclude additional browser traffic. Timings reflect the measured host load; API and official runs overlapped. Per-seat model spend is unavailable. Complete room export, presentation/video, public publication, final submission and official judging remain outside this task.

Stage 3 is authorized to extend a complete copy of this accepted folder. Stage 2 must remain frozen at the tree above. The eventual consolidated report and final package audit cover all four folders.
