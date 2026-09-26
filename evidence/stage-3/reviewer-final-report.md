# Stage 3 independent review — ACCEPT

The Reviewer independently accepts source commit **4b7b0620f3dd645fac18d840a6d612e8f4c6bed6** for local Stage 3 readiness. Its Stage 3 tree is **6f4bee6bec0d5908de7ebe9345290f786b012b63**. No application defect was found in this review. This permits the already-authorized copy of the complete accepted Stage 3 folder into Stage 4; it does not accept Stage 4 or a final submission package.

## Exact source and scope

- Output repository: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper`.
- Parent: `dbb92ecd1f3476002ab5042a5c93ba5517bb8432`, Planner's recorded Stage 2 outcome. Accepted Stage 2 source `2e026c006569b2e749de79b7526f03ae9b6e44e3` is an ancestor.
- Stage 1 remains `0050accbdc6d0457ffdc73de6365158e65c1808b`; Stage 2 remains `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8`. Earlier folders and mandates have no diff from the accepted Stage 2 revision. Mandates tree: `fbfd2dd5db832c375091a0b3a63bb944cd3ec859`.
- Every run checked exact HEAD, clean worktree and earlier trees before and after. `reviewer-source-audit-01.json` also records ancestry, parent, tracked layout, no symlink/submodule modes, no Stage 4 paths and no committed state-export/private-file paths or matches from the bounded credential-shape scan. Such scanning is not a proof against every possible secret.
- Official upstream remains `803560d2a678ace1414465c098eb0ab5380ffade` with no tracked changes. No application, official test, mandate or root documentation was edited by Reviewer.
- Complete inherited/current specifications came from the sequential Planner dispatch and authoritative checkout. Independent design and the 55 API / 11 inherited browser groups were recorded before Stage 3 implementation inspection. The exact clean frozen candidate was identified in Planner's policy/UI evidence message; Reviewer also requested Builder's formal frozen handoff and did not duplicate that request when the transport returned the separate Planner evidence. This report's results come from Reviewer's own runs, not the Planner probe or Builder checks.

## Observed runs

All paths below are relative to `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-3`.

| Evidence | Actual outcome | Measured duration |
|---|---|---|
| `reviewer-api-01` | 55/55 independent groups; 1,789 instrumented HTTP requests; zero failures/errors/5xx | unittest 19.284 s; check command 20.170 s; complete runner 31.404 s |
| `reviewer-browser-01` | 11/11 real Chromium groups; 52 instrumented API setup/control calls plus browser traffic | unittest 21.839 s; check command 22.893 s; complete runner 28.698 s |
| `reviewer-browser-policy-03` | 1/1 additional policy UI group, including awaited HTTP 200 replay; 9 instrumented API calls plus browser traffic | unittest 1.381 s; check command 1.849 s; complete runner 7.222 s |
| `reviewer-official-01/harness` | Stage 1 120/120, Stage 2 25/25, Stage 3 7/7; harness exit 0; claimed Stage 3 | suites 18.29 / 17.88 / 1.13 s; harness command 49.664 s; complete runner 50.251 s |

The independent browser coverage is **12 unique groups**, executed as 11 plus one additional targeted group. Browser requests themselves are not all included in the API instrumentation totals; no invented aggregate request count is claimed. API ordinary-request maximum was 2.215638584 s and test-control maximum 0.140804417 s. Main browser setup/control maxima were 0.054686667 / 0.097942792 s. The final policy-browser supplement maxima were 0.036230042 / 0.088634542 s. Instrumented requests observed zero 5xx.

The official Stage 4 probe collected six tests: **four passed, one failed, one unexecuted** because of official fail-fast. It took 0.80 s and failed `test_series_clock_time_can_be_changed` with 404 instead of 201, demonstrating the missing later-stage endpoint. There were no skips, errors, deselections or xfails. The report's `overshoot` field is null; the separate `stage-4.counts.json`, `stage-4.log` and command output establish that this probe ran and did not pass its whole suite. Its partial passes do not claim Stage 4.

## Independent scope

The API suite includes the inherited 28-group error/auth/privacy/idempotency/atomicity/DST/export matrix, eight combined-table groups, eleven policy/history/series groups and eight additional upgrade/boundary groups. It exercises complete immutable policies, publication/date/tie ordering, accepted cutoff precedence, all resulting fields under the new policy, no-op preservation, optional expected revisions, 50-way policy and amendment races, explanation truth tables, owner-only history/decision including no-token 404, pair history canonicalization, adoption identity preservation, maximum recurring counts, 50 identical adoptions, first failing occurrence, full rollback, permanent exceptions, aggregate series changes and future Berlin/New York gap/fold calendars.

Migration checks independently populate actual Stage 1 and Stage 2 service containers, export in memory, alter the source after export, replace a separately populated Stage 3 destination, retain old sessions/password login/references and exact original create/move receipts, and adopt imported anchors. Current Stage 3 populated policy/history/series exports also round-trip to a separate destination, preserving cancelled occurrences, exceptions and receipts. Repeated and invalid imports are checked without saving snapshots or session tokens.

Browser checks retain the real routes, signup/login/logout, public/owner flows, single and pair availability, disabled unavailable seating, successful repetition, changed-body requests, stale table refusal, out-of-order searches, lost responses before and after commit, same-key recovery, lookup/cancellation, desktop and 375px geometry, long unrestricted names and local assets. Separate tests keep the same open pending browser form and session while importing actual Stage 1 and Stage 2 exports. Rendered desktop, long-name lookup and policy confirmation screenshots were visually inspected. The policy supplement checks published capacity rather than original restaurant-detail capacity, 375px width, accepted duration and an actual server replay after a newer restrictive policy; it records a screenshot.

Source review followed independent authoring. The single lock plus detached candidate and encoding-before-publication transaction boundary, immutable terms/history copying, canonical table sets, receipt precedence, prior-schema validators, bounded stage-only routes, Dockerfile and RUN.md support the observed behavior. This is targeted source assessment, not a formal proof of all possible executions.

## Runtime and provenance

Each independent run builds the exact Stage 3 folder and actual earlier folders. Stage 3 source uses default 8080; destination uses PORT 8097. All source/destination/earlier-service/client containers use an internal Docker network with 2 CPU / 2 GiB, no service mounts, and an explicit outbound connection probe that fails as required. Network inspection confirms `Internal=true`. The API run's four healthy-start measurements were 0.646 / 0.511 / 0.396 / 0.400 s; all later independent healthy starts also stayed below 0.431 s. A separate ordinary published-port RUN.md command-shape smoke passed in 0.381 s for API, 0.388 s for the main browser run and 0.373 s for the final policy supplement. That smoke is not the evidence of network isolation.

The official command was prepared Python `-m harness run --track tablekeeper --repo <absolute output path> --stage 3 --mode isolated --out <new reviewer-official-01/harness>`, run from the authoritative checkout. The evidence-local Docker metadata transport adapter has SHA-256 `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`. It filters preexisting AppleDouble context metadata while preserving ordinary official bytes and harness arguments; original Stage 1 adapter/evidence remains read-only. The official read-only pytest-cache warnings are retained and do not represent skipped tests or suite failure.

## Preserved review limitations and tooling corrections

`reviewer-browser-policy-02` passed the initial extra UI case (1.593 s), but its final retry assertion could observe the existing confirmation before the new response. Reviewer strengthened that assertion to await the actual POST response and require 200 with the original reference, then ran only that changed case in `reviewer-browser-policy-03`. This was a reviewer observation gap, not an application defect; both runs remain preserved and are not counted as two unique cases. A read-only exploratory Python glob encountered an AppleDouble `.py` file and failed decoding it; no official/source file was modified and no application test outcome was inferred from that tool error.

No source repairs were requested for this Stage 3 candidate. Earlier Stage 1 and Stage 2 source failures and reviewer/infrastructure mistakes remain in their original evidence. Shipped checks are partial, supplementary cases are finite, and no hidden judge result is known. Per-seat model spend was not measured. Local independent readiness is distinct from official event acceptance. Stage 4 implementation/review, full four-folder isolated package verification, final root packaging audit, official room export, public publication, presentation/video and event submission are not completed by this report; the operator-only actions remain outside this authorization.
