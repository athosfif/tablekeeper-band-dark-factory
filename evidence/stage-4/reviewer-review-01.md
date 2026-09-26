# Stage 4 independent review — REJECT

Reviewed full revision `d6b3c0fee8af35dbb15bf98e26f62b8c938e86ce`, Stage 4 tree `692eee75727f6df379e0e5c6f9574793dfaf24dd`. Source was clean and unchanged before/after all four reviewer runs below. The one confirmed defect blocks acceptance despite passing shipped checks.

## Confirmed defect: stale confirmation after applied seating plan

Stage 4 requires existing availability, confirmation and lookup screens to reflect an applied plan. On the same open page, book successfully, apply a manager closure moving the reservation, then explicitly submit the unchanged booking form again. The API correctly returns HTTP 200 and its complete original receipt JSON. Current authenticated GET reports the new seating. However, both `confirmation-tables` and `confirmation-details` render the original seating from the receipt.

Independent single case: original table `c` (Garden alcove), current `d` (Chef counter), visible Garden alcove. Pair case: original `[b,a]` (Courtyard + Window nook), current `[c]` (Garden alcove), visible Courtyard + Window nook. Both cases await the actual replay response, verify complete JSON equality with the original receipt, and retain the same reference. No background polling is assumed. Lookup and refreshed availability already reflect the plan.

Source corroboration after independent reproduction: `stage-4/static/app.js` lines 82–85 render the POST receipt directly. Repair only Stage 4. Preserve API receipt semantics and unchanged request body/key; retrieve current authoritative reservation details for the current confirmation. A failed detail refresh after known successful POST must remain distinguishable from booking rejection or an uncertain booking submission. Guard stale asynchronous detail responses when the diner selects another booking.

Reproduction: prepared Python invokes `reviewer_run.py browser <NEW-NAME> --revision <FULL-COMMIT> --stage3-tree 6f4bee6bec0d5908de7ebe9345290f786b012b63 --tests reviewer_browser_checks.BrowserChecks.test_browser_15_explicit_retry_after_plan_shows_current_seating` from the absolute output repository. Tests and screenshots are in the fresh run directories below; no service source is imported into tests.

## Observed evidence

All paths below are relative to `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-4/`.

| Run | Actual result | Test/command/whole-run seconds |
|---|---|---|
| reviewer-api-01 | 75/75 groups; 2,585 instrumented HTTP calls; zero failures/errors/5xx | 25.523 / 26.149 / 34.912 |
| reviewer-browser-candidate-01 | 1 group; both single and pair subcases fail for the defect above; zero errors | 14.195 / 14.993 / 23.449 |
| reviewer-browser-02 | 15 groups; 14 pass, group 15 has two failing subcases; zero errors; 86 instrumented API calls plus browser traffic | 47.971 / 49.442 / 58.965 |
| reviewer-official-01 | Isolated cumulative 120/120, 25/25, 7/7, 6/6; harness exit 0, claimed Stage 4; zero skips/errors/deselections | suites 24.73 / 22.60 / 1.14 / 1.02; command 65.586; whole run 66.514 |

The candidate run repeats group 15; it is not an extra unique case. The browser selection wrapper used FunctionDef rather than AsyncFunctionDef, giving an empty selector; the runner then executed its complete 15-group class. This reviewer invocation mistake is preserved in `reviewer-browser-selection-note.md` and did not skip or alter tests. No source defect is attributed to it.

API maximum ordinary response 2.116796085 seconds; controls 0.245868625 seconds. Browser full-run instrumented maxima 0.066522666 / 0.165840125 seconds (browser traffic not included in this metric). Independent services and clients used internal Docker networks without outbound access, 2 vCPU/2 GiB, no mounts, default PORT 8080 and destination override 8097. Observed ready times were below one second; separate RUN.md host-port smoke reached health in 0.409–1.232 seconds and is not counted as isolated networking proof. Commands, constraints, hashes, health times and cleanup are in each reviewer-run.json and logs.

API coverage includes inherited validation/auth/privacy/idempotency/deep ignored JSON/DST, 50-way races, original receipts and atomic moves, policies/history/series/exception revisions, independently exhaustive deterministic closure objectives and fixed intervals/accepted capacities/prior closures, apply replay/staleness/atomic reads, series amendment rollback and concurrency, actual independently populated Stage 1/2/3 container exports and Stage 4 replacement/imports. Browser coverage includes auth/navigation, accurate singles/pairs, stale searches/table loss/lost responses, same-key recovery across actual earlier-service upgrades, desktop/mobile/offline assets, long names at 375px, policy capacities, closure lookup and availability, and the failed current confirmation requirement. Detailed case definitions are in the archived sources.

Official tests and ordinary upstream content were unchanged. The copied metadata-only Docker context adapter has SHA-256 `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`; its provenance is inherited from the preserved earlier tooling and archived alongside the official run. It filters filesystem metadata only. Stage 4 has no next-stage overshoot suite.

## Immutable boundaries and outcome

- Stage 1 tree `0050accbdc6d0457ffdc73de6365158e65c1808b`.
- Stage 2 tree `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8`.
- Stage 3 tree `6f4bee6bec0d5908de7ebe9345290f786b012b63`.

All earlier trees matched before/after every run. Reviewer changed only new evidence/test files. Builder may repair the concrete defect in a new Stage-4-only commit, then freeze and hand off the full revision and complete requirements for independent recheck. Do not amend/rebase/squash. Final four-folder package verification and Planner-owned final documentation remain pending. This is local independent rejection, not an official judging outcome.
