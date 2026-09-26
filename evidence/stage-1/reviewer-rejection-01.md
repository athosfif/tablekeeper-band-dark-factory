# Rejected revision: f95a5cbbfcbbb64bb8841d7fdcfb74f6150e5d40

Independent source access and clean working tree verified before and after all completed runs. Specification cases were authored before implementation inspection. No service source or official tests changed.

## Defects requiring repair

1. **Rejected create persists a booking.** In `test_21_deep_ignored_body_is_atomic_and_replayable`, send a valid reservation with an ignored JSON field containing 600 nested arrays. HTTP response is 422 `validation_failed`, but the next authenticated GET /reservations returns one newly confirmed reservation. Expected 201 (unknown fields ignored, §3.4); in any rejection, zero new bookings (§1). The planner reported a candidate reproduction; this reviewer independently reproduced it on the exact frozen commit. The error occurs after the reservation append when recursive copying of the receipt fails. Fix the transactional guarantee for create and moves, deep body equality/replay and export/import, without discarding unknown fields from receipt equality.

2. **Fixture numeric wrong types return the wrong error.** `test_19_fixture_numeric_types_and_invalid_ranges` sends each of `slot_minutes`, `reservation_duration_minutes`, `cancellation_cutoff_minutes` and table `capacity` as a string, boolean, array and object (16 subcases). Actual: 422 `validation_failed`. Expected: 400 `malformed_request` under §5. These ordinary fixture fields have no endpoint-specific type exception; preserve 422 for wrong numeric values and the explicit `party_size` exception.

## Reproduction and preserved evidence

From `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER`:

```sh
/Users/athvs/.cache/figueira-band-harness/bin/python -B evidence/official-stage-1/reviewer_run.py independent reviewer-repro-NEW
```

This builds the frozen stage folder and starts separate source, destination and HTTP-client containers on an internal Docker network. Each service has 2 vCPU/2 GiB, no mounted state, and an outbound probe fails as required. The runner copies the independent test source into each evidence run before execution. Tests are `reviewer_spec_checks.py`, derived from the specification, and the defects are methods 19 and 21.

- `reviewer-independent-02/independent.log`: initial 17 groups passed; 601 HTTP requests.
- `reviewer-independent-03/independent.log`: 20 groups; 16 service type-code failures plus one reviewer assertion error. The reviewer incorrectly assumed a fall-back grid's final fitting slot must end exactly at closing; the independent oracle correctly listed the slots. That assertion was corrected to require the actual 90-minute duration and end ≤ closing. Original failure preserved, never attributed to Builder.
- `reviewer-independent-04/independent.log`: 21 groups, 19 passed and 2 groups failed (17 failing assertions/subcases), 747 HTTP requests, zero observed 5xx, normal max 2.621485 s, control max 0.146716 s. The corrected DST test passes. Run exit 1.
- `reviewer-independent-04/reviewer-run.json`: full commands, commit, image build/timings, resource/health logs, clean-tree checks and test-source digest.

## Infrastructure evidence

- Official isolated attempt 01: runner-image build failed on preexisting upstream `harness/._Dockerfile` xattr before any conformance test. Official source remains untouched.
- Attempt 02: transport adapter attempt failed because Docker rejected ambiguous stdin/Dockerfile flags. No tests ran.
- Attempt 03 uses an unmodified ordinary-file USTAR context streamed to Docker, excluding only AppleDouble metadata and Python caches. This changes transport, not official test content. Its result remains separate from this concrete source rejection.
- Independent attempt 01 could not reach a published port on the internal Docker network. The runner was corrected to use a client container on that network; the service was healthy. This was a reviewer-runner setup failure, not a service failure.

Builder owns repairs in new commits. Preserve history and return a full frozen revision for recheck. Stage 1 is not independently ready at this revision.

## Addendum: completed official run and additional reproduction

`reviewer-official-03/harness/report.json` completed in isolated mode on the same revision. Stage 1: **120 collected, 114 passed, 6 failed, zero errors/skips/deselections**, 28.42 s. Harness exit **1**, total command 328.570 s (including runner-image preparation and probe). Although the harness threshold labels this `claimed_stage: 1` (95%), this is not a passing independent review.

All six official failures occur when resetting the two-zone fixture, before DST assertions: valid separate restaurants reuse table IDs, but the service rejects them with 422 instead of 204. `restaurants_from_fixture` enforces an unstated globally unique table-ID restriction, and `overlap` compares table_id without restaurant_id. **Third defect:** accept restaurant-local table catalogues and scope occupancy by restaurant/table pair. `test_25_table_ids_are_scoped_by_restaurant` was added as a regression; `reviewer-independent-06` refused a temporarily dirty working tree, so it contains no test result. The untracked content was unrelated to the service; it was not inspected or changed. This does not establish that Builder had begun repairs. HEAD was still the rejected revision when last checked.

Stage-2 overshoot probe: **25 collected, 0 passed, 1 failed, zero errors/skips/deselections**, with the official fail-fast option stopping after the absent UI failed. 49.04 s. This is the expected absence of Stage-2 UI, not an empty or startup-failed suite. The probe's other 24 collected cases were not run. Report `overshoot: null` must not be described as a numeric probe pass; actual probe evidence is in stage-2.log/counts.

`reviewer-independent-05` executed three additional groups: tests22/23 passed (same entire body on distinct keyed paths, equal JSON numeric values, 50 concurrent exports/moves followed by independent imports); test24 failed. A batch with a 600-level ignored array responds **422 while moving the reservation from t1 to t2**. This confirms the partial-commit defect affects both idempotent endpoints. 121 calls, ordinary max 0.037069 s, control max 0.189620 s, zero 5xx; test time 0.722 s, runner test-command exit 1. The complete source now contains 25 independent groups for repair recheck.

## Verdict and remaining scope

**REJECT. Stage1 is not independently ready at f95a5cbbfcbbb64bb8841d7fdcfb74f6150e5d40.** The three source defects above require Builder-owned new commits and a frozen full revision. Reviewer will recheck the complete25-group source, including depth receipts/import and restaurant isolation, then rerun the final official isolated suite in a fresh evidence directory. No repaired commit has been accepted or implied by this report.

The independent full21-group run's source/destination start-to-health observations were5.026281s and3.968610s; resource logs show2000000000 NanoCPUs,2147483648 bytes,internal network and no state mounts. Default8080 and overridden8097 were reached from a separate container. The stage folder built alone. A separate ordinary published-port RUN.md smoke is prepared in the runner for the repair recheck; it is not yet claimed as completed. The harness's isolated service resource configuration was also inspected and matched2CPU/2GiB with no mounts.

Exact cutoff equality against a moving external clock and already-cancelled behavior after the clock crosses cutoff were inspected in code, with ordinary boundary API tests, not controlled by a nonexistent clock API. Hidden official tests remain unavailable. No external submission, factory gate acceptance, published repository, room export, presentation or video is claimed.
