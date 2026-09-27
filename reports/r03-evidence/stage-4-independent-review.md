# Stage 4 independent review — ACCEPT

Accepted commit: **bb417f29a586fe0771fcc728ab308584f00d5b9a**. Stage4 tree: **2473ec5b52d8ab4ea53e6ce5f75eeb358f2bd719**. Repository tree: **8606f591548771c17e841785a830cab75d4f1b88**. This decision is based on independent executions against the committed image, not Builder assertions. No genuine product defect remains in the exercised scope.

Frozen earlier trees remain stage1 `dfff49710165dc7d568496f1d230b4fc69eb7b2c`, stage2 `b33e79f9bb65ff730b626f9c774afa4653b11e59`, stage3 `3c21f70a1e2d2f2a615c1e1b4a3ab50d2bb699fb`. The reviewer detached clone is clean. No product, root-documentation, official test or accepted-folder edit was made.

## Provenance and independent derivation

The original stage4 executable preparation contained 198 new prepared IDs and zero product executions; its manifest remains SHA256 `af329c1ef4ad167d4c9206bc300f8fafe0bcf7fa7d78fe8273674b0879db4437`. The 22 additional POST/current-GET cases were sealed at09:16:10.799689Z in `supplement-seal.json`, before `source-inspection-start.json`. Their script SHA256 is `e6884d06b80883dca93115d6325aaccfef373297b7e1fc71e8535823c1fb1b0c`. Both original acceptance maps and oracle inputs remain untouched.

The two edited-anchor migration executions instantiate the already sealed original-schedule/import families but their executable expansion was written after inspection. This timing is explicitly recorded in `migration-schedule-boundary.md`; those two executions are not retroactively claimed as part of the executable seal.

`checkout-proof.json`, `runtime-provenance.json`, `html-provenance.json` and `final-integrity.json` bind the clone, served assets and tests to this candidate. Reviewed Docker image: `sha256:ee00d762d8491304fbbe69cce16b226a37c10d4557b8b8e4c8224b6e4590e6b5`. Product containers use 2 vCPU / 2 GiB and only an internal Docker network. Separate ingress helpers expose loopback endpoints for isolated installed Chrome. Browser and API fixtures ran on separate candidate containers when concurrent. Source images were the actual frozen stage1,2,3 images; their IDs and stopped states are recorded. No product networking, external assets or user browser profile was used.

## Official isolated result

Independent cumulative stage4 command:

```sh
REVIEW_DOCKER_SHIM=1 PYTHONDONTWRITEBYTECODE=1 /Users/athvs/.cache/figueira-band-harness/bin/python '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence/reviewer/review-bb417f2/record.py' official-01 '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs' /Users/athvs/.cache/figueira-band-harness/bin/python -m harness run --track tablekeeper --repo '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence/reviewer/review-bb417f2/checkout' --stage 4 --mode isolated --out '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence/reviewer/review-bb417f2/official-01'
```

All 158 required checks passed: 120 stage1 (17.80s), 25 stage2 (26.35s), 7 stage3 (1.26s), 6 stage4 (1.05s). Harness command wall time 116.397575167s; exact command, logs and report are in `official-01.command.json`, `official-01.*` and `official-01/report.json`. Official HEAD stayed `803560d2a678ace1414465c098eb0ab5380ffade`; all 65 tracked official files retained their hashes. The transport shim sends only tracked committed bytes to Docker, excluding macOS sidecars, with context manifests. No official assertions changed. There is no next-stage probe beyond stage4. Planner's final all-folder package gate remains separate.

## Independent results and counting

| Suite | Distinct passing IDs | Final coverage executions | Case elapsed seconds |
|---|---:|---:|---:|
| Inherited API, freshly executed |198|198|54.356628|
| New stage4 API/oracle |174|174|122.394835|
| Inherited installed-Chrome journeys |91|93|186.035000|
| New stage4/POST-current-GET browser |43|43|174.884000|
| Actual stopped-source migration cycles |5|5|26.122516|
| Total |**511**|**513**|**563.792979**|

`case-ledger.json` contains every ID, evidence path, outcome, timing and final-coverage designation. Two inherited IDs each execute twice; these are reruns, not extra distinct cases. The198 inherited API IDs exclude the old opaque-export restaurant-counter observation: stage4 counters are independently verified through public preview responses.

Chronologically there were 689 case executions: 687 passing executions and 2 checker synchronization nonpasses, with 775.243938376 case-seconds. This includes the 174 original API executions before the evidence serializer was stopped, their 174 complete reruns, and the 2 corrected cancellation checks. A separate zero-case launch failure and the post-test aggregation failure are recorded below. The 158 official executions are separate and overlap independent requirements; they are not 511 additional distinct cases. Preparation/oracle selfchecks are not product passes.

## What was verified

The 98 independent planner fixtures (18 hand-derived and 80 deterministic generated fixtures) compare the product against full Cartesian enumeration and a separately implemented backtracking oracle. They check every closure-overlapping confirmed booking, fixed reservations across complete booking intervals, old closures, half-open boundaries, pairs, other restaurants, cancellation, own accepted capacities, and the complete changed-count/unused-seats/reference-sorted rank-vector objective. Preview operational state remains unchanged; failed plans retain opaque export equality. All cases at 6 tables / 4 pairs / 6 bookings solve correctly. Larger inputs legitimately returned planning_limit in these fixtures.

The complete 174-case API rerun made 4278 requests. Maximum measured request time was 0.609976542s. Across 427 preview requests the maximum was 0.026102958s; the maximum-bounds optimum preview was 0.019335625s. Maximum apply time was 0.019353125s. Ordinary requests used a 5-second transport timeout, test-control calls 10 seconds. `api-metrics.json` retains the measurements and `api-02/wire-events.jsonl.gz` retains 4278 indexed, hash-verified sanitized full events.

The protocol and amendment checks cover manager/owner privacy, body validation, exact JSON numbers and huge policy0 capacities, key scopes/replays, stale versus already-applied precedence, immutable original receipts, closure occupancy across all write paths/explanations, immutable reassigned history, unchanged terms/times/identity/exception flags, exactly-once restaurant and affected-series increments, concurrent preview/apply/amend/read/export interleavings and failure rollback. Series checks cover original dates/current seats, permanent exceptions and cancelled members, required optimistic revision, no-op/empty eligible semantics including old cutoff, real-change old cutoff/new policy, per-index non-occupancy priority, DST/calendar boundaries and atomic retry behavior.

The retained browser page/session/pending form survives actual stage-1 single and stage-2/3 single/pair export-stop-import-retry cycles, with original key/body/reference preserved. Stage1 has no browser, so the current page used actual stage1 API traffic; stage2/3 retained their actual old page assets. API source1/2 migrations preserved accounts/tokens/current records and exact old booking/batch receipts, then adopted and amended bookings. Manager repair is unexecuted for these two imports because their old exports have no manager roles and correctly return 403. Source3 preserves histories, policies, series identities, exceptions and cancelled members and supports preview/apply/amend after source shutdown. Two extra single/pair cycles moved the anchor to a different date before export; imported amendments retain original scheduled dates and repaired current seats. No opaque export schema was prescribed or synthesized.

Actual installed Chrome covered current confirmation and lookup after plan application, read-only preview, immutable POST replay with current GET presentation, committed POST plus lost/HTTP 503 current GET, unchanged retry recovery, delayed GET success/error after route/session/selection/guest changes, and explicit confirmation after cancellation. The inherited raw-wire 9007199254740993 single-create/pair-create/lookup repros passed unchanged, alongside nearby values, integral/fractional validation, exact numeric API display, changed-intent keys, policy-capacity/cancellation-term behavior, async contexts and retries. All inherited browser suites were executed on this target; none is carried forward as an old pass.

The 145 screenshots include 375/1440 viewports and long restaurant/table names. Actual keyboard selection/focus and overflow checks pass. Visual inspection of mobile/desktop applied seating confirms warm, coherent restaurant styling, readable hierarchy, clear current seating and visible labels. The selected original form remains available for the required unchanged retry; its confirmation separately displays the current authoritative seating. Static files and the four required HTML routes match committed bytes.

## Preserved failures and corrections

`corrections-ledger.md` and original outputs remain intact. There are **zero genuine product failures** in this review.

1. `browser-current-get-01` ran 22 cases: 20 passed; 2 cancellation assertions sampled before the new current-read/render finished. Both preserved failure screenshots and body captures already show the correctly cancelled confirmation. The v2 checker waits for that same required visible state within the original 7-second timeout. `browser-current-get-03` passes both cases; expectations were not relaxed.
2. `browser-current-get-02` launched no case because the reviewer supplied a misspelled cwd. Its original command/output remain; corrected execution uses03.
3. `api-01` completed 174 PASS records before its final in-memory pretty JSON aggregation grew to approximately 2.9 GiB in the reviewer helper. It was stopped after HTTP work (exit 137, command 332.417991500s). Its stdout/progress and private roundtrip remain. v2 streams full sanitized wire events as gzip JSONL; all assertion/fixture/oracle modules are byte-identical. `api-02` completed 174/174 with exit 0 and command 124.045703708s. The original run is not relabelled as a fully packaged pass.
4. An exploratory no-index folder diff included an AppleDouble file, and an exploratory /static/index.html request returned 401. The authoritative committed tree diff and the four required HTML route hashes were subsequently recorded separately. Neither is a product defect or an independent test case.

## Direct source review and limits

`committed-stage3-to-stage4.diff` contains 8 changed files, 350 insertions / 52 deletions: RUN.md, agreements.py, application.py, domain.py, ledger.py, planning.py, state.py and static/app.js. The API implementation changed materially. Planning filters the complete considered set, uses accepted capacity maps and full-interval domains, and searches exact ranked assignments within fixed bounds. Application and series mutations remain under the service's existing serialized transaction boundary. Ledger logic differentiates diner changes from operator repairs; import logic preserves original schedules using immutable adoption receipts. The browser adds a guarded current GET after the immutable booking receipt. Remaining risks are combinatorial scaling beyond declared bounds, correctness on unenumerated fixtures, and maintenance of migration validation as schemas evolve. These finite tests do not prove hidden-check correctness or all possible scheduling interleavings.

No new management/history screen, polling, stage5 behavior or restaurant-revision endpoint was imposed. Unsupported larger planning inputs may reject with planning_limit. This acceptance is for the exact stage4 product tree; it is not publication, submission, room export, or final package acceptance. Planner owns those remaining gates.

Reproduction entrypoints and complete argv/environment routing are in the top-level `*.command.json`, `run-cumulative-api.py`, `run-cumulative-browser.py`, `run-browsers.py`, `run-migrations.py` and `record.py`. Use fresh output names and recreate the recorded scoped runtime containers before rerunning; saved evidence directories are immutable. Reviewer-only containers/network were removed after diagnostics, with image caches retained (`runtime-cleanup.json`).
