# Tablekeeper — sequential stages 2–4 plan

Status: Stage 3 independently accepted at 4b7b0620f3dd645fac18d840a6d612e8f4c6bed6. Stage 4 is the current authorized phase, starting from its complete copied folder; final four-folder packaging remains pending.

## Accepted baseline and immutable inputs

- Output: /Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper
- Baseline delivery: e5c256641653de82a97222d1126308fbde6188f6 (clean at continuation).
- Accepted Stage 1 source: 0f96bf0cd889959d134ca6f8a5ee3066bbe459f8.
- Immutable stage-1 tree: 0050accbdc6d0457ffdc73de6365158e65c1808b.
- Read-only upstream: /Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs at 803560d2a678ace1414465c098eb0ab5380ffade.
- Complete participant guide (877 lines) and all four specifications (472/240/240/109 lines) read. They define acceptance; shipped tests provide partial evidence.
- Existing generic mandates remain unchanged. All seats use Codex / gpt-6-astra: Figueira Planner, Figueira Builder, Figueira Reviewer.
- Prior Stage 1 report and evidence remain read-only. No implementation belongs in the preparation project.

## Ownership and sequence

1. Planner records this plan, acceptance map, baseline and interpretations, then delivers full task, guide and inherited/current specification text in room.
2. Builder takes shared task #4. Copy accepted stage-1 into stage-2; implement complete browser/combined-table service and focused checks. Commit, provide full requirements and exact revision to Reviewer, then freeze source.
3. Reviewer takes #5. Before implementation inspection, derive independent cases. Verify exact frozen revision, cumulative isolated official checks, additional API and browser checks, populated upgrade and earlier-folder hashes. Report genuine ACCEPT/REJECT with reproducible evidence.
4. Builder repairs actual defects in new commits; Reviewer independently rechecks. Preserve all failures and test-oracle mistakes separately.
5. After explicit Stage 2 acceptance and recorded stage outcome, Builder copies its full folder into stage-3 and extends policies/history/series. Repeat the independent loop, including imports from stages 1 and 2.
6. After explicit Stage 3 acceptance, copy into stage-4 and extend deterministic closure planning/application and series amendments. Repeat independent loop, importing stages 1–3 and preserving each earlier tree.
7. Planner completes root documentation and reports. Reviewer audits the final commit, four folder trees, evidence/claims and complete isolated package checks. Stop after one consolidated final outcome.

No new seats/rooms, human clarification or approval. Existing authorization covers all steps. A genuine blocker is reported with evidence if no authorized path remains. A message timeout is not acceptance; never resend the same request automatically.

## Recorded Stage 2 outcome

- Accepted source: 2e026c006569b2e749de79b7526f03ae9b6e44e3; folder tree 2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8.
- Stage 1 remains tree 0050accbdc6d0457ffdc73de6365158e65c1808b.
- Isolated official: 120/120 Stage 1 and 25/25 Stage 2; expected Stage 3 probe 1 failed, 6 unexecuted.
- Independent: 36/36 API groups and 10/10 browser groups, including populated Stage 1 upgrade in the same open browser.
- Initial 61949b2 was rejected for valid long restaurant names overflowing at 375px despite passing shipped checks. New CSS commit fixed wrapping; independent browser full-flow recheck and Planner's original regression both passed.
- Stage-specific evidence and limits: [STAGE-2-REPORT.md](STAGE-2-REPORT.md).

## Recorded Stage 3 outcome

- Accepted source: 4b7b0620f3dd645fac18d840a6d612e8f4c6bed6; folder tree 6f4bee6bec0d5908de7ebe9345290f786b012b63.
- Stage 1 and Stage 2 trees remain exactly as recorded above.
- Isolated official: 120/120 Stage 1, 25/25 Stage 2 and 7/7 Stage 3. Stage 4 probe: four passed, one missing-endpoint failure, one unexecuted; it did not pass the whole next suite.
- Independent: 55/55 API groups and 12 unique browser groups (11 full plus one targeted), including actual populated Stage 1 and Stage 2 upgrades. No application defect found or source repair requested.
- Planner additionally verified selected-policy capacity displayed truthfully while original restaurant detail stays unchanged.
- Stage-specific evidence and limits: [STAGE-3-REPORT.md](STAGE-3-REPORT.md).

## Product direction

English hospitality product: warm off-white, near-black, restrained dark green, sparing lime, considered type and spacing. Real restaurant and seating labels lead. Search, available/unavailable seating, selection, loading, confirmation, refusal and uncertainty differ in words and appearance. All routes have consistent navigation, visible labels and keyboard focus. Test desktop and 375 CSS px with no page overflow. Fonts and assets work offline. No mock booking, invented metrics/reviews or unrelated landing page. The server is authoritative. Later API features need no extra screens unless necessary to keep surfaced product behavior truthful.

## Acceptance map

The complete specs accompany every handoff. This map groups obligations; it does not replace any requirement.

| ID | Obligation | Independent evidence |
|---|---|---|
| C01 | Every inherited Stage 1 API/error/auth/privacy/idempotency/time/atomicity/snapshot rule, including earlier four repaired defects | Cumulative official suite plus inherited supplementary regressions and source-informed risk review |
| C02 | One self-contained folder/container, no sibling links, 0.0.0.0, default/override PORT, 2CPU/2GiB, healthy <=60s, 50 requests, 5s/10s bounds, offline assets | Standalone Docker context/RUN.md, constrained internal network, blocked egress, observed timings |
| C03 | Immutable earlier folders, full history and generic mandates | Exact accepted commit and Git trees before/after every review; no symlinks/submodules/nested repositories |
| C04 | Atomic export/import/reset, no lost sessions/receipts, independent earlier-service upgrades | Populated source/destination containers; snapshots in memory; source mutations after export; repeat import/replacement and retry |
| U01 | HTML /, /signup, /login, /lookup; all required test IDs; auth errors/current-user/logout on every screen | Browser route/auth navigation and ownership checks |
| U02 | Search exact API singles, per-table per-slot cells, available flag, unavailable inert, labels, closed day/no-slots | Browser and API correspondence across capacities, occupancy and dates |
| U03 | Out-of-order search A/B cannot overwrite B's grid, labels or form | Controlled delayed independent responses for different restaurant/date/party inputs |
| U04 | Signed-in booking, summary, prefilled party, persistent form, exact reference/details; unchanged success replay/new body fresh key | Browser interception and reservation count/receipt comparison |
| U05 | Stale occupied selection: explicit booking-error, refresh, retain inputs, no new confirmation | Competing independent client commits after form opens |
| U06 | Lost response including after commit: nonempty uncertainty only; unchanged retry same body/key; original reference on recovery | Browser abort/proxy race, no cached success, single and pair, same open page during upgrade |
| U07 | Lookup own reference, status exactly confirmed/cancelled, cancel button removed, failure visible | Retained pre-upgrade session/reference, ownership and cutoff |
| U08 | Presentation quality and all visual states; labels/focus/contrast/touch; 375px without overflow | Rendered desktop/mobile screenshots plus keyboard/overflow/browser assertions |
| T21 | Declared unordered pairs only, not transitive; summed capacity; available_options order singles then pairs | API capacity, reversed-pair normalization and pair overlap across members |
| T22 | table_id or table_ids, not both; duplicate validation, >2/undeclared pair errors; response shape, cancelled seeding | Create/PATCH/moves/reset invalid and valid matrices |
| T23 | Combination UI test IDs in declared order, all labels; single compatibility; serializable concurrent occupancy | Browser combinations/recovery and 50-in-flight conflict/retry/move checks |
| P31 | explain=true only; no extra explanation without it; both independent rules every table/order/version | Full capacity x overlap truth table, closed/no-option/DST/policy slots |
| P32 | Owner-only history/decision 404 even without token; monotonic seq/time, created/changed/cancelled fields | No-op, replay, failed amendment and privacy checks; immutable old entries |
| P33 | Manager-only immutable complete policy publication, exact validation/version allocation and effective-date/tie selection | Out-of-order and backdated publication, same-date ties, invalid types/ranges, concurrent/replay writes |
| P34 | Accepted terms snapshot, revision1 creation/seed; old cutoff first, all resulting fields under selected policy; true no-op retains terms/end/history | Policy changes around create/amend/cancel/no-op, expected_revision races and old receipt replay |
| P35 | Pair histories use table_ids and declared order; reversed pair no-op | Single/pair transition matrix with policy-selected capacity |
| R31 | Adopt own editable confirmed non-adopted anchor, count2..12, interval1..4; anchor unchanged | Auth/error matrix, idempotency precedence, anchor exact identity/history/timestamps |
| R32 | Generated local calendar weeks, per-date policy/DST, first failure index, full rollback | DST gaps/folds, policy boundaries, occupancy failures, no counters/history/receipt changes |
| R33 | Series current states, fixed references/indices, exceptions permanent only for real diner edits; cancel independent | Individual amend/cancel/repeat/no-op + series revision aggregation and list/history |
| R34 | Collective moves use per-item expected revision/old cutoff/new policy; aggregate series/restaurant increments once | Mixed real/no-op, multiple same-series moves, error precedence, simultaneous swaps |
| R35 | Upgrade stages1/2 into3 retains sessions/references/old original receipts; adopted imported bookings work | Actual populated exports from each earlier accepted service and rejected-import rollback |
| O41 | Manager preview closure interval/limits, no mutation except stored plan; considered vs fixed bookings | Authorization, offset/half-open bounds, size limits, no-plan rollback, snapshot comparison |
| O42 | Deterministic objective: minimum moved, then unused seats under each booking's accepted terms, then rank vector by reference | Independent bounded exhaustive oracle, fixed bookings/earlier closures/pairs/capacity changes |
| O43 | Apply stale revision/already-applied/replay precedence, atomic closures and assignments; identities/terms/times preserved | Concurrent applies/other writes, cross-restaurant non-invalidation, no partial reads |
| O44 | Restaurant revision baseline0 and exact once-per-real-operation accounting; preview/replay/no-op/failure none | Whole-operation revision matrix including adoption/moves/series/plan |
| O45 | Moved-only reassigned history/table_ids/plan_id; series once-per-plan, preserve exceptions/scheduled dates | Mixed series/ordinary considered bookings, unchanged members and post-closure availability/explain |
| O46 | Owner series amend required revision/from_index/time; skip cancelled/exceptions; original scheduled dates; policy/cutoff | Validation/stale precedence, eligible/no-op/empty sets, original dates after individual edits |
| O47 | All-or-nothing series amendment, no exceptions, aggregate revisions once; same-revision concurrent real edits | Error order, unlisted/conflicting/closed occupancy, retries after later writes and independent upgrade |
| O48 | Stage4 imports stages1–3, including moved/cancelled series and all original receipts/history | Actual populated migrations, browser regression and state replacement |
| F01 | Full-spec handoffs, explicit frozen revisions, independent outcomes, failures/history preserved, accurate claims | Room exchanges, per-run metadata, stage reports and final audit |
| F02 | Complete cumulative final isolated checks and expected overshoot distinguished; full four-folder package | Unique directories and actual counts/statuses; no skipped/empty/startup-error passes |

## Interpretations from the written requirements

- Stage 3's “without explain keeps stage 1 shape” means no explanation fields; inherited stage-2 available_options remains required.
- Stage 3 names restaurant revision before Stage 4 defines its exposure/accounting. Track aggregate changes consistently; no premature Stage 4 endpoints in stage-3.
- Reversed approved pairs denote the same set and canonicalize to declared order. Unknown fields still belong to receipt JSON equality.
- Old receipts imported from earlier stages retain their original JSON responses, even when current resource responses gain newer fields.
- Original scheduled series dates are immutable schedule metadata, distinct from individually amended current starts.
- Closure feasibility checks the full occupied booking interval against fixed bookings and closures, and uses each booking's accepted capacities. Considered bookings are all confirmed bookings overlapping the proposed interval, even those not currently on the closing table.
- Optional extra UI is not required for policy/series/operator endpoints; any behavior surfaced must remain understandable and real.
- Shipped stage claim is partial local evidence, not event acceptance. No final submission, publishing or private room-export action is authorized.

## Evidence and reporting

Evidence roots: /Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-2, official-stage-3 and official-stage-4. Each run gets a unique role/name and records source commit, tree hashes, exact commands, timings, results and screenshots. Never store tokens/private exports. Stage 1 evidence is read-only.

Use prepared Python /Users/athvs/.cache/figueira-band-harness/bin/python and Docker /Applications/Docker.app/Contents/Resources/bin/docker, both binary directories in process PATH. From readonly upstream: python -m harness run --track tablekeeper --repo '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper' --stage N --mode isolated --out '<new evidence directory>'. Final package uses --all. Record any metadata-only transport adapter without changing official ordinary content.

Final report includes exact baseline/accepted commits and folder hashes, actual official and independent counts, measured timings, repairs, remaining limits, readiness of all four folders and operator tasks (official room export, presentation/video, public repository and submission). Per-seat model spend is unavailable unless measured evidence becomes available; do not invent an estimate.
