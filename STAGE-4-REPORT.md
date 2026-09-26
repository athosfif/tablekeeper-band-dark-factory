# Stage 4 result and complete package verification

Stage 4 is independently ready locally. Reviewer accepted `8c6df7f369f0041798abf8de0e10c0babf501df5` after a genuine confirmation-screen rejection and a new repair commit. All four cumulative stage folders passed the complete supplied isolated package run. This is local independent readiness, not official judging, publication or submission.

## Revisions and scope

- Accepted Stage 3 source/baseline: `4b7b0620f3dd645fac18d840a6d612e8f4c6bed6`, tree `6f4bee6bec0d5908de7ebe9345290f786b012b63`.
- Stage 4 implementation parent: `bedeb731df4114ce5466a912825605efa547d333`, the root-only Stage 3 outcome documentation.
- Rejected Stage 4 source: `d6b3c0fee8af35dbb15bf98e26f62b8c938e86ce`, tree `692eee75727f6df379e0e5c6f9574793dfaf24dd`.
- Accepted Stage 4 source: `8c6df7f369f0041798abf8de0e10c0babf501df5`, tree `e4bae830ae426197911968153c97c4ef06f9e40d`.
- Stage 1 remains `0050accbdc6d0457ffdc73de6365158e65c1808b`; Stage 2 remains `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8`; Stage 3 remains its tree above. Mandates remain `fbfd2dd5db832c375091a0b3a63bb944cd3ec859`.

The complete standalone service is in [stage-4/RUN.md](stage-4/RUN.md). It adds manager closure previews and atomic application with a deterministic three-part objective, plus owner recurring amendments. All prior booking, policy, history, combination, browser recovery and state-upgrade requirements remain. Management operations are API-only, as permitted.

## Actual independent results

Evidence root: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-4`. Full verdict: `reviewer-final-report.md`.

| Run | Result |
|---|---|
| `reviewer-api-repair-02` | 75/75 groups, 2,585 instrumented HTTP requests, zero failures/errors/5xx. Test31.379s, command32.223s, whole run42.908s. Maximum ordinary/control latency3.489738668/0.195503209s. |
| `reviewer-browser-repair-03` | 17/17 browser groups, zero failures/errors. Test36.542s, command37.828s, whole run44.999s. 91 instrumented setup/control calls plus additional browser traffic. |
| `reviewer-package-01` | Complete four-folder official isolated `--all` run, exit0, command202.442s, whole run203.385s. Exact clean accepted source revision before/after. |
| `planner-replan-02` | Nine independent optimizer/application scenarios, 88HTTP, zero5xx, max0.077765s; maximum preview0.012840s. Executed on rejected parent; API/solver unchanged by the final browser-only repair. |
| `planner-closure-ui-02` | Original browser defect reproduction passes on exact clean accepted source: same reference and complete original POST200 receipt, current seating shown in confirmation and lookup. Screenshot preserved. |

The two Planner runs used constrained ordinary published-port containers; independent isolation proof comes from Reviewer runs. Planner's optimizer includes the full6-table/4-pair/6-booking limit, per-booking accepted capacities, fixed full-interval occupancy, half-open adjacency, declared pair ordering, empty plans and infeasible-key reuse. Its self-checks are not counted as application tests.

The 75 independent API groups include inherited errors/auth/privacy/deep JSON/receipts/DST, 50-way races, atomic moves and exports, effective policies/immutable terms/history, series exceptions/revisions, exhaustive closure objective checks, previous closures, stale and atomic application, recurring amendment rollback/concurrency, and populated exports from actual accepted Stage1/2/3 services into independent Stage4 destinations. Browser tests cover required routes, visual states, desktop/375px including long labels, stale searches and competing writes, lost-response recovery, unchanged retries through earlier-service upgrades, policy capacities, closure effects and the repaired confirmation/details-read boundaries.

Final isolated services and clients used2CPU/2GiB, internal networks with blocked outbound probes, no mounts, default8080 and custom8097. All final independent services reached health within0.699s. Separate ordinary RUN.md smoke observations were0.435s and1.348s. Runtime assets are local. Tokens and state exports remained in process memory.

## Complete isolated four-folder package

The package run invoked the prepared Python from the authoritative checkout, with the absolute output repository and a fresh output directory. Every applicable cumulative suite completed with zero failures/errors/skips/deselections/xfails. These are575 passing conformance executions across folders, not575 distinct test definitions.

| Folder | Suite1 | Suite2 | Suite3 | Suite4 | Local shipped-check claim |
|---|---|---|---|---|---|
| stage-1 |120/120,20.69s|—|—|—|1|
| stage-2 |120/120,16.95s|25/25,16.62s|—|—|2|
| stage-3 |120/120,21.75s|25/25,21.19s|7/7,1.06s|—|3|
| stage-4 |120/120,21.91s|25/25,27.54s|7/7,1.28s|6/6,1.14s|4|

Expected next-stage probes are separate: Stage1→suite2 collected25, passed0, failed1, unexecuted24 (11.51s); Stage2→suite3 collected7, passed0, failed1, unexecuted6 (0.22s); Stage3→suite4 collected6, passed4, failed1, unexecuted1 (0.82s). All three stopped on the genuine missing later-stage feature under official fail-fast. Stage4 has no next suite. No unexecuted probe case is counted as passing.

Evidence: `reviewer-package-01/harness/summary.json`, per-folder `report.json`, suite logs/count files, `verified-summary.json` and `reviewer-run.json`. The copied metadata-only Docker transport adapter has SHA256 `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`; ordinary official source/tests/flags remained unchanged. Original Stage1 evidence remains read-only.

## Review changed the result

The initial source passed75 API groups and all158 cumulative shipped checks, but Planner found stale confirmation seating after applied closure and explicit retry. Reviewer independently reproduced it for singles and pairs and rejected the source (`reviewer-review-01.md`, `reviewer-browser-candidate-01`, `reviewer-browser-02`). The API's original receipt was correct; the UI needed current authoritative details.

New commit8c6df7f changed only Stage4 app.js, a focused test file and RUN.md. It reads current reservation details after acknowledged booking success, preserves original request identity/receipt/reference, distinguishes a failed detail refresh from a refused or uncertain booking, and discards delayed details when selection changes. Reviewer independently rechecked singles/pairs, aborted detail reads and stale responses; all17 browser groups passed. Planner reran the original reproduction.

Builder's initial frozen source had49/49 focused groups,1,182 instrumented calls plus browser traffic,26.570s and max2.1174s. Its repaired browser run `builder-repair-02` passed9/9 groups,79 direct calls plus browser traffic,24.405s; committed app/test hashes matched the tested files. These author checks supplement independent verification.

Preserved tooling mistakes remain distinct from source defects: Builder's first closure fixture used the wrong UTC offset; its first repair runner nested synchronous Playwright sessions; Planner's first optimizer runner used Request.method instead of get_method and ran zero cases; Reviewer selected FunctionDef instead of AsyncFunctionDef and consequently ran its entire browser class. No failed run was relabeled a pass, and none of these authoring errors was invented as another product rejection.

## Final packaging and limitations

Root documentation is finalized after source acceptance. Its exact delivery commit and independent packaging verdict are recorded in the final coordinator room report and the subsequent Reviewer packaging evidence; the source results above remain attributed to their tested revisions/trees. Service source remains frozen; any genuine audit defect returns to the same review/repair loop.

Hidden official checks are unavailable; tested schedules/interleavings are finite and source inspection is not formal proof. Per-seat tokens/model spend are unavailable. The official full-room export and privacy review, presentation/video, publication, clean-clone submission checks and event submission remain operator tasks. The absence of an official room export prevents claiming complete submission gates, but does not change the independently verified service results.
