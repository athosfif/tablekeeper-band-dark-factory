# Stage 4 independent acceptance

**ACCEPT** full revision `8c6df7f369f0041798abf8de0e10c0babf501df5`, Stage 4 tree `e4bae830ae426197911968153c97c4ef06f9e40d`.

The previously rejected parent `d6b3c0fee8af35dbb15bf98e26f62b8c938e86ce` retained correct immutable API receipts but showed stale confirmation seating after a manager applied a closure plan. The repair now retrieves the current reservation using the acknowledged original reference. Independent single and combined-table reproductions pass without changing the original POST receipt, request body or idempotency key. Known booking success remains distinct from a failed details read; late reads cannot overwrite newer selections. No unresolved implementation defect was observed in this review.

## Exact revision and scope

The source was explicitly frozen, clean and at the handed-off full revision before and after each final reviewer run. The repair changed only `stage-4/static/app.js`, `stage-4/test_confirmation.py` and `stage-4/RUN.md`. API/server/solver/snapshot code remained byte-identical to the rejected parent, and was nevertheless independently rerun at the final revision. All earlier source trees, generic mandates and ordinary upstream tracked content remained unchanged; all accepted commits and the rejected parent remain ancestors. No symlinks, submodules or nested Git repositories were found. See `reviewer-repair-audit-01.json` and each run's before/after logs.

| Folder | Accepted source | Immutable tree |
|---|---|---|
| stage-1 | 0f96bf0cd889959d134ca6f8a5ee3066bbe459f8 | 0050accbdc6d0457ffdc73de6365158e65c1808b |
| stage-2 | 2e026c006569b2e749de79b7526f03ae9b6e44e3 | 2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8 |
| stage-3 | 4b7b0620f3dd645fac18d840a6d612e8f4c6bed6 | 6f4bee6bec0d5908de7ebe9345290f786b012b63 |
| stage-4 | 8c6df7f369f0041798abf8de0e10c0babf501df5 | e4bae830ae426197911968153c97c4ef06f9e40d |

Mandates tree: `fbfd2dd5db832c375091a0b3a63bb944cd3ec859`. Official input: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs`, revision `803560d2a678ace1414465c098eb0ab5380ffade`. Complete participant guide and all four specifications governed review; shipped tests are partial evidence.

## Final independent runs

Evidence root: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-4`.

| Run | Actual outcome | Test / command / total seconds |
|---|---|---|
| reviewer-api-repair-02 | 75/75 groups, 2,585 instrumented HTTP calls, zero failures/errors/5xx | 31.379 / 32.223 / 42.908 |
| reviewer-browser-repair-03 | 17/17 groups, zero failures/errors; 91 instrumented API calls plus browser traffic | 36.542 / 37.828 / 44.999 |
| reviewer-package-01 | Full four-folder official isolated run; every folder claims its numbered stage | command 202.442 / total 203.385 |

API maximum ordinary response: 3.489738668 seconds; test controls: 0.195503209 seconds. Browser-run instrumented maxima: 0.059942334 / 0.147051459 seconds; these metrics exclude browser-issued traffic. Final independent services and clients ran with 2 vCPU/2 GiB on internal Docker networks, without runtime outbound access or mounts. Default PORT 8080 and destination override 8097 were exercised. All final independently started services reached health within 0.699 seconds. Separate RUN.md published-port smoke checks reached health in 0.435 and 1.348 seconds; those smoke checks do not constitute offline networking evidence.

Independent API coverage includes inherited auth/privacy/error/type/JSON equality/idempotency precedence, deep ignored fields and original receipts, 50-way concurrency, atomic moves and exports/imports, DST gaps/folds and absolute intervals, dated policies and immutable accepted terms/history, series adoption/exceptions/cancellation/revisions, independently exhaustive closure objective comparisons, full-interval fixed occupancy and earlier closures, accepted capacities per booking, preview/apply/stale/replay/atomic reads, series amendments/rollback/concurrency, and independently populated actual Stage 1/2/3 service exports into fresh replacement destinations. Imported current plans, closures, series and all receipt types are exercised.

Independent browser coverage includes required routes/auth/navigation, exact grid correspondence and unavailable choices, single/pair bookings, successful unchanged replay and changed form identity, competing table loss, lost POST responses before/after commit, same-key recovery in the same page across actual earlier-stage upgrades, stale search responses, policy-selected capacities, cancellation/refusal, desktop and 375px views with long labels, applied-plan lookup/availability, current confirmation after explicit original-receipt replay, detail-read failure after acknowledged success, and late detail responses after new seating selection. Rendered screenshots and executable test snapshots are preserved. See `reviewer-repair-source-and-visual-notes.md` for visual/source corroboration.

## Complete four-folder official isolated result

All cumulative suites below ran completely with zero failures, errors, skips, deselections, xfails or unexecuted cases. There are 575 passing cumulative conformance executions across the four folders, including 158 against the final Stage 4 folder.

| Folder | Suite 1 | Suite 2 | Suite 3 | Suite 4 | Claimed stage |
|---|---|---|---|---|---|
| stage-1 | 120/120, 20.69s | — | — | — | 1 |
| stage-2 | 120/120, 16.95s | 25/25, 16.62s | — | — | 2 |
| stage-3 | 120/120, 21.75s | 25/25, 21.19s | 7/7, 1.06s | — | 3 |
| stage-4 | 120/120, 21.91s | 25/25, 27.54s | 7/7, 1.28s | 6/6, 1.14s | 4 |

Expected next-stage probes are separate from those passing cumulative suites:

- Stage 1 against suite 2: 25 collected, 0 passed, 1 failed, 24 unexecuted after fail-fast; 11.51s.
- Stage 2 against suite 3: 7 collected, 0 passed, 1 failed, 6 unexecuted; 0.22s.
- Stage 3 against suite 4: 6 collected, 4 passed, 1 failed, 1 unexecuted; 0.82s.
- Stage 4 has no next-stage probe.

The probes did not pass the entire next suite. They are not incomplete passing conformance suites. The full package command exited 0, and every report is completed. `reviewer-package-01/verified-summary.json`, `harness/summary.json`, per-folder reports/counts/logs and exact runner metadata preserve the evidence. This `--all` run includes the required final cumulative Stage 4 isolated verification; a redundant separate final `--stage 4` run was unnecessary.

The metadata-only Docker context adapter SHA-256 is `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`. It is copied from the preserved earlier review tooling and archived in the package run. Only filesystem metadata is filtered from transport; ordinary official source/tests/flags are preserved. Original official checkout and earlier evidence remain untouched.

## Reproduction

From absolute working directory `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper`, use prepared Python `/Users/athvs/.cache/figueira-band-harness/bin/python -B` and the absolute evidence-root `reviewer_run.py`:

```text
reviewer_run.py api <NEW-NAME> --revision 8c6df7f369f0041798abf8de0e10c0babf501df5 --stage3-tree 6f4bee6bec0d5908de7ebe9345290f786b012b63 --stage4-tree e4bae830ae426197911968153c97c4ef06f9e40d
reviewer_run.py browser <NEW-NAME> --revision 8c6df7f369f0041798abf8de0e10c0babf501df5 --stage3-tree 6f4bee6bec0d5908de7ebe9345290f786b012b63 --stage4-tree e4bae830ae426197911968153c97c4ef06f9e40d
reviewer_run.py package <NEW-NAME> --revision 8c6df7f369f0041798abf8de0e10c0babf501df5 --stage3-tree 6f4bee6bec0d5908de7ebe9345290f786b012b63 --stage4-tree e4bae830ae426197911968153c97c4ef06f9e40d
```

The package runner invokes the prepared Python from the authoritative checkout with `-m harness run --track tablekeeper --repo <absolute-output-repo> --all --mode isolated --out <new-directory>`. Docker and prepared Python binary directories are set in that process PATH; HOME/CODEX_HOME are unchanged. Every run archives its commands, exact test source hashes, timings and outcome. Tokens and state exports remain in memory.

## Preserved failures and remaining work

`reviewer-review-01.md`, `reviewer-browser-candidate-01`, `reviewer-browser-02`, `reviewer-api-01` and `reviewer-official-01` retain the rejected parent review. The original defect failed both single and pair subcases while the shipped suite passed. The reviewer wrapper's FunctionDef/AsyncFunctionDef selection mistake is separately documented in `reviewer-browser-selection-note.md`; it caused the complete browser suite to execute rather than omitting a repeated case, and was not a source defect. Builder and Planner exploratory instrumentation/oracle mistakes remain in their own preserved evidence and are not counted as independent reviewer passes or product defects.

Builder source work ends at this accepted revision. Planner-owned final README/FACTORY/plan/stage reports and their final committed packaging audit remain pending. Their later root-only commit must preserve all four accepted source trees and mandates; the completed package evidence remains attributable to these exact trees. Official room export, presentation/video, public publication and event submission remain operator tasks outside this authorization. This is independent local readiness on the complete written requirements and observed tests, not official judging or a hidden-test guarantee. Model spend was not measured and is unavailable.
