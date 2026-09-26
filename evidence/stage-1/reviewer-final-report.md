# Independent Stage 1 review — accepted

**ACCEPT `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`. Tablekeeper Stage 1 is independently ready on the available specification-based evidence.** No unresolved implementation defect was observed. This is a local independent review, not official event acceptance, publication or submission.

Reviewer: Figueira Reviewer. Completed 2026-09-26. Shared assignment: room `b11e30b4-d1a2-4a83-ba35-e97ca6bfc9e3`, task2.

## Revision and provenance

- Output repository: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper`; self-contained implementation in `stage-1/`.
- Exact HEAD was verified before and after both full runs and the additional routing check. Full repository status was clean. A final `git diff --exit-code 0f96bf0cd889959d134ca6f8a5ee3066bbe459f8 -- stage-1` also returned0. This review did not accept an uncommitted implementation.
- Accepted `stage-1` Git tree: `0050accbdc6d0457ffdc73de6365158e65c1808b`. Planner's announced later root-documentation update is outside this source verdict; a future packaging check may establish tree equality without attributing these test runs to a different tested HEAD.
- Read-only authority: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs`, revision `803560d2a678ace1414465c098eb0ab5380ffade`. Tracked content remained unchanged; preexisting AppleDouble metadata was left in place.
- All reviewer artifacts below are under `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`. Reviewer edited only independent checks, runner/transport support and evidence. No implementation, official tests, planner plan, mandates or history were changed.
- The acceptance design and first17 HTTP groups were authored before implementation inspection. Later groups came from full-spec gaps, real failures and bounded repair changes. Builder's checks were not used as independent acceptance proof.

## Actual results on the accepted revision

| Check | Result | Timing / evidence |
|---|---|---|
| Independent full suite | **27/27 groups passed**,955 HTTP requests,0 observed5xx, exit0 |13.082s unittest;13.888s test-container command;33.947s complete run. [Log](reviewer-independent-09/independent.log), [commands/timings](reviewer-independent-09/reviewer-run.json) |
| Additional encoded-reference check | **1/1 group passed**,13 HTTP requests,0 observed5xx, exit0 |0.187s unittest;0.710s test-container command;18.807s complete run. [Log](reviewer-independent-10/independent.log), [commands/timings](reviewer-independent-10/reviewer-run.json) |
| Official isolated Stage1 | **120 collected,120 passed,0 failed/errors/skipped/deselected/xfailed** |20.94s suite; harness exit0;40.534s command. [Report](reviewer-official-05/harness/report.json), [log](reviewer-official-05/harness/stage-1.log), [counts](reviewer-official-05/harness/stage-1.counts.json) |
| Required Stage2 overshoot probe |25 collected,0 passed,1 failed,0 errors/skips/deselections/xfailed; **24 did not execute after official fail-fast** |13.87s. Expected missing browser UI (`search-button` selector timeout); browser test actually ran. [Log](reviewer-official-05/harness/stage-2.log), [counts](reviewer-official-05/harness/stage-2.counts.json) |

Independent total: **28 distinct groups verified in a27-group full run plus1 targeted run;968 instrumented HTTP calls**. Group counts are test groups with multiple assertions and subcases, not a claim of968 separate acceptance cases. The source was unchanged between the full and targeted runs.

Official output: `highest_contiguous:1`, `claimed_stage:"1"`, share1.0, isolated mode, run ID `db0ad0f68d0642ed862edb28ad92a2de`. Suite digest `0eb86668d630de3c3c58e51d43135ec08a9cfe341742bff904db86ed4c287312`. The report labels provenance `working-tree`; independent before/after checks establish that this working tree exactly matched the committed revision. The report's `overshoot` field is null, so the actual Stage2 outcome above is taken from its separate log/count files. One read-only pytest-cache warning did not prevent any Stage1 case from running.

## Resource, runtime and standalone delivery evidence

The independent runner built directly from the standalone `stage-1/` context, using only its Dockerfile and included files, without Compose or manual setup. The measured build was0.951s with Docker's existing build cache available. Fresh runtime containers had no mounted source or state volumes. The RUN.md build/start contract also passed a separate published-port smoke check using PORT8080; health was observed within0.424223s. Name, image tag and host port were varied to avoid collisions.

Two separate service containers each ran with `--cpus=2 --memory=2g`. Docker inspection reported `NanoCpus=2000000000`, memory2147483648 bytes and empty mounts for both. One used default8080; the other used `PORT=8097`. They communicated with the independent HTTP client on an internal Docker network; the service required no companion service. [Source constraints](reviewer-independent-09/constraints-0.log), [destination constraints](reviewer-independent-09/constraints-1.log), [internal network](reviewer-independent-09/network-internal.log).

The internal network flag was true, and an outbound TCP connection probe failed as required. [Outbound evidence](reviewer-independent-09/outbound-probe.log). The official final run separately used its isolated mode, which enforces the prescribed offline network and resource limits.

Observed start-to-healthy upper bounds, including Docker command overhead, were3.497216s and4.341741s, below60s. In the full independent suite, maximum ordinary HTTP latency was **3.351785s** (limit5s), and test-control maximum **0.121120s** (limit10s). The targeted check maxima were0.035301s and0.105469s. These measurements include the50-in-flight cases; no observed request produced5xx. Containers and temporary networks were cleaned up by the runner.

## Specification coverage

[Acceptance design](reviewer-acceptance-design.md), [coverage map and inspected mechanisms](reviewer-coverage-notes.md), and [independent HTTP source](reviewer_spec_checks.py) document all11 specification sections and all active plan rows. Main checks include:

- Fixture replacement, seeded login/bookings, opaque64-character IDs and invalid lengths, ordinary wrong-type400 versus invalid-value422 and endpoint-specific exceptions, ignored fields/queries, UTF-8 JSON and offset-bearing timestamps.
- Authentication/signup/login, password boundaries, multiple concurrent tokens, private owner reads and writes, and required public/test-control endpoints. Source inspection confirms salted scrypt password hashing and constant-time comparison; exports retain hashes rather than input plaintext.
- Whole parsed-body idempotency, ignored nested values, key order/whitespace, numeric equality and bool/number distinction, user/path scopes, inspected method scope, parse/auth precedence, used-key precedence before field/resource validation, failed-key reuse and original responses after change/cancel/import.
-50 simultaneous competing creates,50 identical creates,50 identical batch retries,50 amendments to one destination and50 concurrent logins. Successful identical writes have exactly one201; retries return200 with the original receipt.
- Half-open adjacency, absolute occupancy, capacity filtering, empty availability slots, local opening grids and closing bounds, arbitrary past/leap dates, descending reservation lists, successful/failed/no-op PATCH, immediate/repeated cancellation and cutoff against the current old start.
- Both specified Berlin/New York DST gaps and first folds, unique repeated-hour availability, absolute90-minute durations and offset opening grids.
- Atomic swaps and8-item cycles, unchanged listed occupancy, batch shape/duplicate/ownership/restaurant checks, error precedence in input order, old cutoff before requested changes, non-occupancy errors before overlap, whole-value no-ops and preserved original batch receipts.
- Export/import into an independent process without source mounts or addresses; hashed-password login, multiple existing tokens, config ordering, identities/status/timestamps, original create/batch receipts, failed keys, replacement of destination credentials, repeat import, invalid-state rollback and reset clearing imported state.25 concurrent snapshots interleaved with25 moves remained internally consistent when imported.
-600-level and1,100-level ignored JSON structures, malformed deep syntax, atomic create/batch behavior, receipt equality/replay and portable deep receipts. Restaurant-local table IDs remain independent across occupancy and import.
- Opaque restaurant IDs with escaped slashes, Unicode and literal percent sequences remain publicly addressable; unknown IDs give404. The final targeted group verifies percent-encoded reservation references retain owner privacy and auth, decode exactly once, and support PATCH/cancel without changing other values.

Implementation inspection corroborates one lock around state access, detached candidate mutation, rollback on exceptions, and complete response encoding before committing a successful mutation. The final routing diff recognizes encoded segments before decoding identifiers once.

## Reproduction

From `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER`, the executed commands were:

```sh
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py independent reviewer-independent-09
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py independent reviewer-independent-10 --tests SpecChecks.test_28_encoded_reference_keeps_ownership_and_auth
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py official reviewer-official-05
```

Choose new directory names for a rerun; the runner refuses existing directories. Run09 preserves the exact27-group test source (SHA256 `ae4201a6322ba37501654037568cdda35bb3e331c406f1fd92888f8a976e5bd8`). Run10 preserves the28-group source (SHA256 `e623e1af7ffb3b2e9b687b6108c08db9bf3aa7cd91de186cb5b8cc7d761b8108`). The current source includes all28 groups. No service code is imported into these HTTP tests. All exports and tokens stayed in process memory; logs contain aggregate results and synthetic fixtures only.

The official command, run from the authoritative checkout, was:

```sh
PATH="/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1/reviewer-docker-bin:/Applications/Docker.app/Contents/Resources/bin:/Users/athvs/.cache/figueira-band-harness/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 /Users/athvs/.cache/figueira-band-harness/bin/python -m harness run --track tablekeeper --repo "/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper" --stage 1 --mode isolated --out "/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1/reviewer-official-05/harness"
```

The first PATH entry is the documented Docker-context transport adapter. On this host, the ordinary Docker context walker failed reading xattrs from preexisting upstream `._Dockerfile`. The adapter intercepts only the official harness runner-image build and streams ordinary context files unchanged as USTAR, excluding AppleDouble metadata and Python cache files. It preserves ordinary file content/modes and all other Docker calls/flags; it does not alter tests or application code. The source checkout remains untouched. Adapter SHA256: `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`; a copy is retained in `reviewer-official-05/reviewer-docker-adapter.py`. This transport qualification is part of the evidence, not hidden as a service repair.

## Defects, repairs and preserved failures

| Reviewed revision | Independently observed result | Repair verification |
|---|---|---|
|`f95a5cbbfcbbb64bb8841d7fdcfb74f6150e5d40`|Rejected: valid ignored deep JSON returned422 but persisted create/batch mutations;16 ordinary fixture wrong-type subcases returned422 instead of400; global table-ID uniqueness rejected valid separate restaurants and occupancy was not restaurant-scoped. Official120 collected,114 passed,6 failed.|Builder repaired in new commit `bea7a7553ac240050dead490e0f42525d0a81f08`; independent regression groups19/21/24/25/27 now pass. [Original rejection](reviewer-rejection-01.md), runs `reviewer-independent-04`, `reviewer-independent-05`, `reviewer-official-03`.|
|`bea7a7553ac240050dead490e0f42525d0a81f08`|Earlier three defects repaired; official120/120 passed. Independently rejected because accepted `branch/one` and Unicode slash IDs returned401 on public percent-encoded detail instead of200; unknown encoded IDs returned401 instead of404. Run07:25/26 groups passed,3 failing subcases in the remaining group.|Builder's bounded routing repair in current `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8` passes group26 and new protected-reference group28. [Original rejection](reviewer-rejection-02.md), runs `reviewer-independent-07`, `reviewer-official-04`.|

All failures and timings remain preserved. Reviewer runner/setup issues are distinguished from service defects: `reviewer-independent-01` could not reach an internal-network published port and was corrected by using an independent client container; `reviewer-official-01`/`02` were context-transport startup failures with no passing tests; `reviewer-independent-03` contained an overstrict reviewer DST closing assertion, corrected from exact closing equality to the specified closing bound and absolute duration; `reviewer-independent-06` refused temporary unrelated untracked repository content and ran no tests. No pass is inferred from any setup failure. Builder's earlier packaging-permission failure is preserved separately in builder-owned evidence and is not claimed as a reviewer reproduction.

## Limits and final disposition

Hidden official tests are unavailable. Finite tests cannot exhaust all interleavings or unbounded input sizes. Exact cutoff equality with a moving real clock, and repeated cancellation after the clock crosses the cutoff, are supported by explicit inspected branches plus at/after-current-minute API checks, not a fabricated clock-control endpoint. Method scoping is also inspected because only POST paths require keys in Stage1. The Stage2 probe intentionally stops after its first genuine missing-UI failure;24 collected cases were not executed.

Within those stated limits, full stage coverage, the final official isolated run and meaningful supplementary specification checks are complete. **No unresolved Stage1 blocker remains; accept the exact revision above.** Shared task2 can be completed. Stop at Stage1. Factory eligibility checks, final room export, presentation/video, public repository publication and competition submission are separate outcomes and are not claimed here. Model spend was not measured or estimated.
