# Tablekeeper Stage 1 — verification and delivery report

The Stage 1 JSON API is implemented and passed the final independently executed checks. The run resolved every reproduced service defect. This report describes local stage readiness; it does not claim official event acceptance or submission. Stage 2 was not started.

## Scope and committed source

Tested API revision: **`0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`**.

Tested `stage-1` Git tree: **`0050accbdc6d0457ffdc73de6365158e65c1808b`**. The final documentation commit changes only repository-root documentation; the delivery audit compares this tree with that commit so documentation is not represented as a new application test run.

Authoritative input revision: `803560d2a678ace1414465c098eb0ab5380ffade`. Planner read the complete participant guide and Stage 1 specification and recorded their hashes in `planner-baseline.json`. The official guide, specification, harness and tests remained unchanged. The original three generic mandates and preparation history remain intact.

The service provides signup/login with hashed passwords and concurrent bearer sessions; public restaurant browsing and availability; idempotent reservation creation; owner-private list/lookup/cancel/amend; atomic multi-reservation moves; DST-aware, half-open occupancy; reset and portable state export/import including original retry receipts. Unknown fields, opaque IDs, explicit error codes and invalid-input rollback are included in the acceptance map.

Everything required to build and serve is in `stage-1/`, with its own Dockerfile and [RUN.md](stage-1/RUN.md). Runtime uses one container, listens on `0.0.0.0`, defaults to PORT 8080, accepts an override, and needs no outbound network. State is deliberately ephemeral. There are no submodules, symlinks, UI or later-stage implementation.

## Actual final results

Evidence root: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`.

| Check | Result on the tested API revision | Evidence under that root |
|---|---|---|
| Official isolated Stage 1 | 120 collected, 120 passed; zero failures, errors, skips or deselections. 20.94 s suite time; harness exit 0. | `reviewer-official-05/harness/report.json`, `reviewer-official-05/harness/stage-1.log`, and `reviewer-official-05/reviewer-run.json` |
| Independent specification suite | 27/27 groups, 955 requests, no observed 5xx; 13.082 s. Ordinary-call max 3.351785 s, control-call max 0.121121 s. | `reviewer-independent-09/independent.log`, `reviewer-independent-09/reviewer-run.json`, per-run test-source copy |
| Builder focused validation | 21 groups, 551 instrumented HTTP requests plus two raw in-memory exports; 9.086 s; maximum measured HTTP latency 2.3057 s. One group tests local injected exceptions; HTTP groups use two Docker service containers. | `builder-repair-containers-02/`, `builder-repair-02.md` |
| Deployment and isolation | Standalone stage-folder builds; default and custom ports; two independent service containers, 2 vCPU/2 GiB each, no state mounts, internal network and failed outbound probe. | Independent run constraint, network, health, build and smoke logs |
| Scope probe | Stage 2: 25 collected, 0 passed, 1 failed at the absent UI; official fail-fast left 24 unexecuted. 13.87 s. This expected probe failure does not invalidate Stage 1 or authorize Stage 2. | `reviewer-official-05/harness/stage-2.log` and count artifact |

The official runner emitted read-only pytest-cache warnings while still completing the suite. No skipped or startup-failed suite is counted as passing. The final report's `highest_contiguous` and `claimed_stage` are 1 on the **shipped** checks; hidden official checks are unavailable.

## Independent coverage and repair trail

`plan.md` maps every specification section to acceptance obligations. `reviewer-acceptance-design.md` records cases derived before implementation inspection, and `reviewer-coverage-notes.md` maps independent checks to the plan. The final suite additionally tests deep-body parsing/serialization/replay, concurrent snapshots and moves, restaurant-local table IDs and percent-encoded opaque IDs.

| Revision | Preserved outcome and resulting change |
|---|---|
| `c427c3ba23d830e2986624417a10bf554bf26daa` | Initial API. Builder container startup exposed non-root source-permission failure. |
| `f95a5cbbfcbbb64bb8841d7fdcfb74f6150e5d40` | Permission repair. Independent rejection found partial commits after deep-body errors, wrong fixture-type error codes and incorrectly global table IDs. Official Stage 1 was 114/120, not a passing review. |
| `bea7a7553ac240050dead490e0f42525d0a81f08` | Transaction/JSON/type/table-scope repairs. Official 120/120 passed, but independent review still rejected opaque-ID routing (25/26 groups; three failing subcases). |
| `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8` | Route matching before identifier decoding. Final official 120/120 and independent 27/27 passed. |

The actual fixes are general: detached candidate state and response encoding before publication, rollback on exceptions, iterative JSON value handling, ordinary-versus-special type validation, restaurant/table-pair occupancy, and route segmentation before decoding an opaque identifier once. Planner reproduced two candidates; Reviewer independently confirmed them against commits and found additional defects. Builder owns all source repairs. Original commits, failures and timing logs remain; nothing was squashed, rebased or amended.

Reviewer also preserved its own setup failures and corrected a faulty DST assertion. Those are identified as reviewer/tooling issues rather than manufactured implementation defects. The source-rejection reports are `reviewer-rejection-01.md` and `reviewer-rejection-02.md`.

## Reproduction

From the output repository:

```sh
docker build -t tablekeeper-stage-1 stage-1
docker run --rm --name tablekeeper-stage-1 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper-stage-1
```

From the authoritative checkout, run the supplied harness with a **new** evidence directory. On this macOS volume, the recorded transport adapter avoids pre-existing AppleDouble/xattr failures without changing official files:

```sh
PATH="/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1/reviewer-docker-bin:/Applications/Docker.app/Contents/Resources/bin:/Users/athvs/.cache/figueira-band-harness/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 /Users/athvs/.cache/figueira-band-harness/bin/python -m harness run --track tablekeeper --repo '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper' --stage 1 --mode isolated --out '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1/NEW-RUN-NAME'
```

The adapter is `reviewer-docker-bin/docker` under the evidence root. Its first two unsuccessful attempts are preserved in `reviewer-official-01` and `reviewer-official-02`; they executed no conformance tests. Later runs use unchanged ordinary source bytes in a USTAR build context. A clean checkout without the volume metadata can use the provided Docker executable directly.

Independent reproduction from the preparation workspace uses the retained reviewer runner, again with a new name:

```sh
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py independent reviewer-recheck-NEW
```

## Remaining limits

- This is local verification of Stage 1. Official judging, public submission, room export and presentation/video submission are not performed or claimed.
- State does not survive process/container restart, as explicitly permitted. Export/import is the implemented state-transfer contract.
- Tests cover the specified 50-way contention and documented cases; finite runs do not establish every possible interleaving or unlimited state size. The transactional design was also inspected independently.
- The macOS source-volume transport workaround and pytest-cache warnings are documented above. The application itself needs no external runtime service.
- No known reproduced Stage 1 service defect remains in the final independent checks. No private state export, generated token or real user credential was committed. All fixtures are synthetic.
- Actual per-seat model spend was unavailable and is not estimated. Measured run intervals and recovery costs are in `FACTORY.md` and the raw evidence.

The final in-room delivery disposition identifies the complete documentation commit and independently confirms that its stage tree is the tested tree above. The API, source history and evidence stop at Stage 1.
