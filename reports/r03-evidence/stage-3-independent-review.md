# Stage 3 independent review — ACCEPT

**ACCEPT `6b75841c243ea4722be08834526545ea847bad27`.** No unresolved product defect was found in the executed official, independent API and installed-Chrome checks. This is an exact-candidate gate, not proof of hidden-check completeness. Stage4 implementation/copy remains the coordinator's gate decision.

| Identity | Verified value |
|---|---|
| Full candidate | `6b75841c243ea4722be08834526545ea847bad27` |
| Repository tree | `03bce1ef702ca0f522e9bed12b9481746b0c424d` |
| Frozen stage1 tree | `dfff49710165dc7d568496f1d230b4fc69eb7b2c` |
| Frozen stage2 tree | `b33e79f9bb65ff730b626f9c774afa4653b11e59` |
| Stage3 tree | `3c21f70a1e2d2f2a615c1e1b4a3ab50d2bb699fb` |
| Independently built image | `sha256:a890eeac4d40b91740bc3e0a76f6abd8d4597b22fda6cbf5587c7075ce6235a7` |
| Official checkout HEAD | `803560d2a678ace1414465c098eb0ab5380ffade` |

## Preparation and provenance

The independently derived stage3 map/approach remained the basis. Executable preparation is separately sealed at `../stage-3-executable-preparation/preparation-manifest.json`, SHA256 `4a8ddc4da65a7e2abffa6ed9849f39c7076dcf1e6c21d42b47ed8132a2c1da0c`. It records zero stage3 source reads, product requests, browser launches or product passes at sealing. The exact commit handoff arrived during preparation; no claim is made that these scripts predate Builder's implementation. First source inspection was **after** that seal; see `first-source-inspection.txt`. Preparation selfchecks remain separate from product acceptance.

`checkout/` is a detached clone at the full hash. `revision.json` verifies all trees. The actual Git-tree diff is `tracked-stage2-to-stage3.diff`: nine files, 483 insertions/61 deletions (new policies, ledger and agreements modules; application/domain/state; RUN.md; app.js/app.css). The initial filesystem `stage2-to-stage3.diff` also saw host-generated AppleDouble files; those are not committed source changes and are not the authoritative diff.

All six served assets matched their committed bytes (`provenance-final.json`), including unchanged exact-json.js. Five evidence-local Docker transport manifests were byte-verified against their respective candidate/official Git blobs. The official harness context is correctly verified against the official checkout, not against product Git. All **65 official tracked files** match official Git; official and detached product tracked status are clean. No stage4 folder is committed. Product/root docs/official tests/Git index were not edited. Sealed prior maps, rejected reports and accepted folders remain unchanged.

Two candidate containers used 2 vCPU, 2 GiB, only an internal Docker network, no mounts, and PORT 8080/9090. Old source images were the accepted stage1 `ec96785a3aaa611e8519d09869cade8ffddb9224` image `65848d04...` and stage2 `e44838741cc906fbcae88e4248b5dc850af90e7c` image `f14448a3...`; full image IDs are in `runtime-proof.json`. A separate fixed-destination evidence relay exposed localhost ingress to Chrome; product containers had no outbound network. Container logs are empty for both candidate services. Reviewer containers/network were removed after evidence collection; images and evidence retained.

## Official isolated gate

Fresh `official-01/`; full invocation, start/end timestamps and wall time are in `official-01.command.json`:

```sh
REVIEW_DOCKER_SHIM=1 PYTHONDONTWRITEBYTECODE=1 /Users/athvs/.cache/figueira-band-harness/bin/python record.py official-01 '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs' /Users/athvs/.cache/figueira-band-harness/bin/python -m harness run --track tablekeeper --repo '<THIS_REVIEW>/checkout' --stage 3 --mode isolated --out '<THIS_REVIEW>/official-01'
```

`<THIS_REVIEW>` is the absolute directory containing this report. The record file contains literal expanded paths. Evidence-local `bin/docker` transports tracked bytes only; it does not modify official suites or product code.

| Required suite against stage3 candidate | Result | Pytest time |
|---|---:|---:|
| Stage1 | 120/120 | 18.55 s |
| Stage2 | 25/25 | 17.44 s |
| Stage3 | 7/7 | 1.19 s |
| **Required total** | **152/152** | |

Full harness wall time **85.969078 s**, including build/start, old-source upgrade fixtures and the next-stage probe. Expected stage4 probe is separate: six collected, four passed, one failed (`POST /series/{id}/amend` returned 404 rather than future-stage 201), one unexecuted after fail-fast; **0.93 s**. This is not a stage3 defect or stage4 acceptance. Read-only pytest-cache warnings are preserved.

## Independent results and counts

**290 distinct case IDs have passing evidence: 199 API + 91 browser/hybrid.** Final coverage uses **328 passing executions**: 199 API +129 browser/hybrid, including two inherited duplicate-ID repetitions and 36 policy-overlay reruns. These repetitions are not new distinct cases. Every final case was exercised on this candidate image; no earlier stage's pass was merely carried forward as current execution.

Chronological totals are different: **413 case executions, 408 passing executions and five preserved nonpassing checker/ingress executions**, with **313.268002 s** summed process wall time for those runs. There were also three startup-aborted inherited invocations (zero cases) totaling 1.088803 s. The interrupted `api-stage3-02` contributes its two observed passing cases and its 1.655042 s, but no complete suite result. `execution-summary.json` lists IDs and preserves which executions establish final coverage. There are 114 actual Chrome screenshots; they are evidence artifacts, not 114 separate cases.

| Run | Executions | Pass / nonpass | Wall seconds |
|---|---:|---:|---:|
| api-stage3-01 | 82 | 78 / 4 | 35.901663 |
| api-stage3-03 | 82 | 82 / 0 | 25.741963 |
| api-additions-01 | 6 | 5 / 1 | 3.121609 |
| api-additions-02 | 1 | 1 / 0 | 0.735267 |
| independent-01 | 63 | 63 / 0 | 8.577891 |
| supplemental-02 | 8 | 8 / 0 | 6.634004 |
| numeric-02 | 15 | 15 / 0 | 2.850313 |
| pairs-02 | 25 | 25 / 0 | 4.238895 |
| api-stage3-02 | 2 | 2 / 0 | 1.655042 |
| browser-01 | 26 | 26 / 0 | 40.537763 |
| browser-extra-01 | 10 | 10 / 0 | 14.427409 |
| browser-boundaries-01 | 2 | 2 / 0 | 3.365645 |
| caption-browser-01 | 2 | 2 / 0 | 11.583424 |
| large-party-repro-01 | 3 | 3 / 0 | 4.384997 |
| numeric-browser-01 | 24 | 24 / 0 | 39.193334 |
| browser-overlay-01 | 26 | 26 / 0 | 40.936732 |
| browser-extra-overlay-01 | 10 | 10 / 0 | 15.476874 |
| browser-stage3-01 | 16 | 16 / 0 | 24.368187 |
| browser-additions-01 | 10 | 10 / 0 | 29.536989 |

### Genuine failures and checker/setup corrections

No genuine product failure survived reproduction in this review. All initial failures remain inspectable in their original files:

- `api-stage3-01`: 78 passed, four nonpassing. Two 50-way schedules encountered a host-ingress connection closure. Repeating the unchanged schedules directly inside the internal Docker network passed; both services emitted no errors. This establishes direct service behavior; it does not hide the relay observation or claim its root cause was proven.
- The other two failures were Python comparison mistakes for ambiguous DST times: fixed-offset datetimes were compared directly with fold-sensitive ZoneInfo datetimes. Actual raw starts used the correct first occurrence and ends used absolute duration. The corrected checker compares UTC instants **and explicit offsets**. Both pass. Original checker is `series_checks.original.py`.
- `api-stage3-02` wrote results directly to the mounted evidence filesystem and stopped on `FileNotFoundError` after two passing cases. The next helper wrote temporary results internally and copied them out through a hashed Docker tar stream (`api-stage3-03-transport.json`). Complete direct run: 82/82.
- `supplemental-01`, `numeric-01`, `pairs-01` aborted before cases because their inherited helper expected `/evidence/independent.py`. Corrected mount location only; unchanged assertions passed 8/8, 15/15, 25/25 in -02. These three inherited Python scripts retain their original /evidence helper path and are run using the recorded Docker mount, not the prepared host runner.
- `api-additions-01`: five passed; seeded case accidentally passed `(token, ref)` to a `(ref, token)` helper and correctly received 401. Correct argument order passed in `api-additions-02`. Original checker is `review_additions.original.py`. Its original diagnostic contains a synthetic token used as a URL reference and is private test evidence.
- One local provenance-collection attempt used the wrong root for an official build context; corrected root selection verified all bytes. No product case occurred during that collection failure.

`checker-corrections.md` preserves chronology. Product source was unchanged for all rechecks. Earlier stage2 numeric REJECT reports and e448387 ACCEPT evidence retain their original hashes and attribution.

## What was exercised

The 82 new API cases plus six coverage-completion cases exercise publication permissions/default manager absence, required fields/types/ranges and exact numerics, immutable policies/version order, effective-date selection and version ties, local date rather than UTC date, original detail remaining fixture shape, complete accepted snapshots, old cutoff in both directions, real changes adopting all resulting policy rules, no-op retention/editability, optimistic revision validation/stale precedence/concurrency, canonical single/pair histories and decision/privacy, cancelled history, explain truth tables/order/completeness/omission, and retained original receipts.

Recurrence covers unchanged single/pair anchors, per-occurrence policies and capacities, count/interval boundaries, first failing index including earlier occupancy ahead of later capacity, rollback at several indices with reusable keys, gaps/folds in both required zones (future calendar fixtures), leap day/year rollover, same-key and different-key concurrency, individual and batch permanent exceptions, cancellation independence, one series increment per affected batch, no-op/failure/replay stability, and batch versus PATCH optimistic conflicts. Concurrent batch/series reads and opaque export/import snapshots remain coherent.

Actual frozen stage1 and stage2 exports preserve accounts, sessions, references, statuses/timestamps, original booking and move receipts and failed-key reuse; imported reservations can be adopted. Stage3 export/import preserves policies, series, exception/cancelled state, histories and original receipts across all new write paths. Imported pre-stage3 history is observed as a baseline; no unrecorded past event count or timestamp is invented. A later actual change appends correctly. Seeded confirmed/cancelled records retain policy0/revision1 and roundtrip.

Restaurant revision has no required public stage3 accessor. Source audit found one shared lock around dispatch/read/snapshot and copied responses; new booking, real amendment/cancellation, policy publication, adoption and batch paths increment at the appropriate commit boundary; no-op/failure/replay paths do not. The additional **implementation-specific** export observation checked reset0 → create1 → replay/no-op1 → policy2 → adoption3 → whole batch4 → replay4 → cancel5 → repeat5, while unrelated Q changes independently. This observation uses the discovered internal field only; it imposes neither an export schema nor a stage4 endpoint. Series and reservation revisions are asserted through their specified public APIs.

The 111 cumulative API cases rerun prior boundary, concurrency, exact JSON, idempotency, atomic move, DST and combination checks. The 65 distinct inherited browser/hybrid cases (67 executions) rerun signup/login/routes, authoritative grid states, single/pair booking/lookup/cancel, conflict preservation, duplicate submission, response-loss recovery, same-body/key retries versus changed intents, exact-number neighboring values and the three original raw-wire numeric repros, navigation/session/selection identity guards, stale success/error/cleanup, long content, keyboard, labels/focus/contrast and 375/1440 overflow. The main/extra schedules were repeated with equivalent published policies; legacy import portions explicitly replace that overlay with the old exported state.

Sixteen new stage3 Chrome journeys cover policy-driven capacities/grid/terms at both widths and seating modes, policy refusal, recurrence occupancy and independent anchor cancellation, accepted cancellation cutoff versus new policy, out-of-order policy searches, lost committed responses retaining original policy receipts, and actual stage2 browser page/session/pending form migration in both seating modes. The same old DOM input and raw body/key survive import; later requests use the candidate, recover the original reference, and lookup succeeds. No stage1 UI is invented: its cumulative recovery uses the explicitly labeled compatible-client adapter.

Ten additional Chrome journeys verify automatic refreshed availability **without a manual search** after capacity refusal, preserved form/inputs and no false confirmation, selected unavailable text visibility, late policy refusals after selection/route/session changes, and delayed cancellation of one recurring occurrence while another is displayed. Visible identity/status is compared with authoritative reservation/series state. Browser page-error arrays remained empty.

## Presentation observation

I visually inspected actual candidate screenshots `browser-stage3-01/screenshots/S3-UI-policy-grid-book-375-true.png` and `...1440-true.png`. The warm restaurant presentation, serif hierarchy, consistent green primary controls, deliberate spacing and combined-seating labels remain coherent with long names and changed capacities. Mobile is vertically long with many slots, but tested controls/content remain usable without page overflow. Confirmation shows the accepted policy's cutoff. Actual Tab/Enter journeys and focus checks passed at 375/1440. Pair-caption gold contrast remains approximately **5.31525:1** on its tested background; shared-gold measurements and CSS byte proof are in `caption-browser-01/caption-browser-01.json`. This is targeted accessibility evidence, not full WCAG certification.

## Commands and limits

`*.command.json`, each inherited browser directory's `command.json`, `run-cumulative.py`, `run-remaining.py`, and `checks/README.md` provide prepared command guidance; the recorded successful invocations provide exact executable commands, paths and timings. API commands use the supplied harness Python and HTTP only, with max 50 concurrent requests. Chrome commands use `/Users/athvs/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node` and its supplied Playwright module, `channel: chrome`, headless isolated contexts. All output directories are distinct; original failed outputs were not reused.

Preparation copies are frozen separately. `checks/` contains only the documented review-side corrections/additions; no Builder tests or product module imports are used by independent checks. The API stdout/event results, browser JSON/screen captures, command records, runtime proof and final manifest make this review inspectable.

Executed coverage is substantial but finite: not every combination of unspecified multi-fault precedence, all dates/time zones, key/path/value cross-products, cutoff millisecond boundaries, browser engines or assistive technologies was enumerated. Source-stop portability was not separately fault-injected after export; real different-process imports and source audit verified no source process/address dependency. No polling, cross-tab synchronization, reload recovery or new history/series screen is required or claimed. No future-stage product pass is claimed. Hidden-check correctness is not inferred from shipped-check passes.

**Disposition: ACCEPT for the exact full commit and stage3 tree above.** Coordinator may use this gate for stage4 authorization; reviewer did not copy or implement stage4.
