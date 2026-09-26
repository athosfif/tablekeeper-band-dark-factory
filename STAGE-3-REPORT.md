# Stage 3 result

Stage 3 is independently ready locally. It extends the accepted browser/combined-table service with effective-dated policies, immutable accepted terms and history, revision checks and recurring agreements. Reviewer accepted the first frozen candidate; no source defect or repair was manufactured.

## Revisions

- Accepted Stage 2 source/baseline: `2e026c006569b2e749de79b7526f03ae9b6e44e3`, tree `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8`.
- Stage 3 parent: `dbb92ecd1f3476002ab5042a5c93ba5517bb8432`, recording the Stage 2 outcome in root documentation.
- Accepted Stage 3 source: `4b7b0620f3dd645fac18d840a6d612e8f4c6bed6`, tree `6f4bee6bec0d5908de7ebe9345290f786b012b63`.
- Stage 1 remains tree `0050accbdc6d0457ffdc73de6365158e65c1808b`; Stage 2 remains the tree above. Mandates remain `fbfd2dd5db832c375091a0b3a63bb944cd3ec859`.

The full standalone service and reproducible commands are in [stage-3/RUN.md](stage-3/RUN.md). Each final run verified exact HEAD and a clean worktree before/after. No Stage 4 routes or sibling dependencies were introduced in this folder.

## Actual results

Evidence root: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-3`.

| Evidence | Result |
|---|---|
| `reviewer-api-01` | 55/55 independent groups; 1,789 instrumented HTTP calls; zero failures/errors/5xx; 19.284s unittest, 20.170s check command. Maximum ordinary/control latency 2.215638584/0.140804417s. |
| `reviewer-browser-01` | 11/11 Chromium groups, 21.839s; 52 instrumented setup/control calls plus additional browser traffic. |
| `reviewer-browser-policy-03` | One additional unique policy/browser group, 1.381s; nine instrumented API calls plus browser traffic. Actual POST replay awaited and verified 200/original reference. |
| `reviewer-official-01/harness` | Isolated Stage 1 120/120, Stage 2 25/25, Stage 3 7/7. Suite times 18.29/17.88/1.13s; harness command 49.664s, exit 0. Zero fail/error/skip/deselect/xfail in graded suites. |
| Same official invocation, Stage 4 probe | Six collected: four passed, one expected missing-amend-endpoint failure, one unexecuted under fail-fast; 0.80s. It did not pass the entire next suite and does not claim Stage 4. |
| `builder-run-02` | 37 focused groups, 21.403s unittest /21.901s command; 551+106+185 instrumented calls, with additional browser traffic. Separate from independent proof. |
| `planner-policy-ui-01` | Exact clean-commit product check: original detail retained capacities2/4, selected policy exposed6/1 and pair7, browser correctly displayed Seats6. Screenshot and public-value result retained; ordinary published-port test, not isolation evidence. |

The independent browser total is 12 unique groups, executed as 11 plus one targeted supplement. Browser calls are not fully counted by the API instrumentation, so no total across all traffic is inferred.

## Coverage and runtime

The 55 API groups comprise 28 inherited groups, eight combined-table groups, eleven policy/history/series groups and eight migration/boundary groups. They cover exact errors and privacy, full parsed-body receipts, concurrency and atomic moves, DST and half-open intervals, complete immutable policies and date/version ordering, accepted cutoff/no-op/revision rules, histories and owner-only decision access, pair canonicalization, recurring adoption and rollback, exceptions, cancellation and aggregate revisions. Actual accepted Stage 1 and Stage 2 containers supplied populated in-memory exports to separate Stage 3 destinations. Old sessions, hashed login, references and original receipts survived; imported anchors were adopted. Same-stage snapshots preserve policies, histories, recurring members and exceptions.

Browser cases include prior booking/lookup/auth flows, refused stale selections, lost responses and exact retries, late search responses, same open signed-in form during both earlier-service upgrades, desktop/375px geometry and long names. The additional policy case checks effective capacity, accepted duration and original receipt after a newer restrictive policy. Rendered screenshots remain in the browser run directories.

Independent services/client ran with 2 CPU/2 GiB each, internal networking, blocked outbound probe and no service mounts; default8080/custom8097 were exercised. API health observations for the four service containers were0.646/0.511/0.396/0.400s. Standalone ordinary published-port RUN.md smoke passed in0.381s for API mode,0.388s for browser mode and0.373s for the final supplement. Isolation is established by the internal-network runs, not by those smoke checks.

The official run uses the evidence-local metadata-only Docker adapter copied from the read-only Stage 1 tooling. Ordinary official files/tests and harness arguments remain unchanged. Full command/source hashes and constraints are recorded in each `reviewer-run.json`; source/provenance audit is `reviewer-source-audit-01.json`. No token or state export was saved.

## Review decisions and limits

Full verdict: `reviewer-final-report.md`. Independent test design preceded source inspection. No application repair was requested. `reviewer-browser-policy-02` preserved an initial passing supplemental case whose final assertion could see an old confirmation too early; Reviewer strengthened it to await the actual HTTP response and reran only that case as03. It is one unique case, not two. A read-only exploration encountered an AppleDouble file; that tooling error is not an application failure. Earlier real source failures remain in previous-stage evidence.

The separate probe logs/counts are authoritative for the Stage 4 probe even though the main harness JSON overshoot field is null. Hidden tests remain unavailable, tested interleavings are finite, and source inspection is not a formal proof. Model spend was not measured. This is local independent readiness, not official acceptance or submission.

The existing authorization now permits a complete copy into Stage 4. Earlier folders remain frozen. Final four-folder verification and root packaging audit are still pending. Official room export, presentation/video, public publication and event submission remain operator tasks outside this run.
