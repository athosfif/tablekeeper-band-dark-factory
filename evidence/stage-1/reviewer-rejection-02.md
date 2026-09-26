# Rejected repair revision: bea7a7553ac240050dead490e0f42525d0a81f08

Exact HEAD and clean repository verified before and after both completed full checks. The earlier rejection of `f95a5cbbfcbbb64bb8841d7fdcfb74f6150e5d40` remains intact. Reviewer changed no implementation or official test files.

## Repair verification

All three earlier defects are repaired in independent HTTP checks:

- Ordinary numeric fixture types now return400 `malformed_request`; invalid values and party_size exceptions retain422.
-600-level ignored-body creates and batch moves succeed with their receipts, replay correctly and export/import into an independent container. No previously observed422/partial mutation remains in these cases.
- Separate restaurant catalogues may reuse table IDs; their occupancy, cancellations and imported state remain separate.

The implementation inspection corroborates detached candidate state with rollback on exceptions, response encoding before successful return under the lock, iterative JSON cloning/equality/encoding, and restaurant/table pair overlap.

## Remaining defect: opaque restaurant IDs lose the public detail route

Planner's candidate was independently reproduced against this exact committed revision in `test_26_opaque_restaurant_ids_remain_publicly_addressable`:

1. Reset a valid fixture whose restaurant ID is `branch/one`:204.
2. Public `GET /restaurants` lists `branch/one`.
3. Public `GET /restaurants/branch%2Fone`: actual401 `unauthenticated`; expected200 with that restaurant.
4. Equivalent Unicode ID `分店/一` also fails. A literal percent-bearing ID can be looked up, but the percent-encoded slash in an unknown related ID returns401 rather than404 `not_found`.

Section3.4 allows opaque fixture IDs up to64 characters; Section8 makes restaurant details public. Once a fixture ID is accepted, percent encoding must preserve it as a single path segment. Current server code decodes the whole route before pattern matching, turning an encoded ID slash into route structure. Recognize the route's encoded segment first and decode the resource ID only after selecting the route. Preserve auth on protected endpoints, decode once, and retain public404 for unknown IDs. Do not restrict accepted IDs merely to hide the defect.

Reproduce from `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER`:

```sh
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py independent reviewer-opaque-NEW --tests SpecChecks.test_26_opaque_restaurant_ids_remain_publicly_addressable
```

## Actual results

- `reviewer-independent-07`:26 groups,25 passed/1 failed (3 failing subcases);919 HTTP requests,zero observed5xx;10.193s tests; ordinary maximum2.551836s/control0.113820s. Command exit1. Full source snapshot and sha256 retained in run directory.
- `reviewer-official-04/harness/report.json`: isolated Stage1 **120/120 passed**,zero failures/errors/skips/deselections;17.97s. Harness exit0,total command35.125s. Suite digest matches prior run. This shipped-check result does not resolve the supplementary opaque-ID failure.
- Stage2 probe:25 collected,0 passed/1 failed,zero errors/skips/deselections; official fail-fast stops after missing UI;12.03s. The other24 cases did not execute; no Stage2 feature is implemented or authorized.
- Two independent service containers:2CPU/2GiB each,no state mounts,internal Docker network with failed outbound probe,default8080 and override8097. Observed startup/health3.613638s and3.431482s.
- RUN.md build from the standalone stage folder passed; ordinary published-port smoke (`PORT=8080`) healthy in0.324732s. Build1.111s. All runner commands are preserved in `reviewer-independent-07/reviewer-run.json`.

## Verdict

**REJECT bea7a7553ac240050dead490e0f42525d0a81f08: Stage1 is not independently ready.** Repair the remaining route defect in a new commit, then supply its full frozen revision. Recheck all independent groups and run the final official isolated harness in a new directory. A targeted independent deep-decoder grammar/receipt round-trip group was additionally authored because this repair introduces a JSON container decoder; its result is recorded separately when complete.

All evidence paths are under `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`. Exports/tokens stayed in memory. The documented AppleDouble transport adapter preserves ordinary official file bytes; official tracked files remain read-only. This report concerns local API verification, not official event acceptance or submission.

Supplementary decoder check completed: `reviewer-independent-08/independent.log`,group27 **passed**,25 HTTP requests,0.193s test duration,ordinary max0.034047s/control0.096056s,zero5xx. It covers1,100 nested arrays,escaped strings,bool-vs-number receipt mismatch,seven malformed JSON forms with unchanged state,failed-key reuse and raw snapshot transfer to an independent process preserving the original receipt. Command exit0; the same full revision stayed clean. The complete independent source now has27 groups for the next revision.
