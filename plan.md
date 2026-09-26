# Tablekeeper stage 1 — implementation and acceptance plan

Status: Stage 1 implemented and all final application checks passed on `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`. Official isolated Stage 1: 120/120. Independent specification groups: 27/27, 955 requests, zero observed 5xx. See `STAGE-1-REPORT.md` for evidence, repairs and limits. Final documentation packaging is checked separately without changing the tested stage tree.

The only dispatched stage is stage 1, the HTTP JSON API. No browser UI or later-stage capability is authorized. The source of truth is the complete participant guide and complete stage-1 specification at upstream revision `803560d2a678ace1414465c098eb0ab5380ffade`. Passing the shipped checks is partial evidence, not official acceptance.

## Boundaries and provenance

- Read-only inputs: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/official-dark-factory-wearedevs/docs/participant-guide.md` and `tablekeeper/spec/stage-1.md` in that checkout. Both were read completely before decomposition. The upstream revision was verified. Existing AppleDouble metadata files are left untouched.
- Output repository: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper`; initial HEAD `9e02c181e3bcefdf3abbe272ba777eed614b8256`, initially clean, containing generic mandates and documentation only.
- Service and its independently runnable image: output repository `stage-1/` only.
- Evidence: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`; every harness run gets a new directory. Keep original failures, logs and timings.
- No changes to official inputs/tests, global configuration, credentials or unrelated projects; no purchases, publication or submission. Synthetic test accounts only. Never commit state exports or bearer tokens. Preserve mandates and append commits; no amend, squash or rebase.

## Ordered delivery and ownership

1. Planner owns this requirements baseline, acceptance map, interpretation decisions and final evidence assessment.
2. Builder owns `stage-1/`, a self-contained Dockerfile, RUN.md, focused tests and implementation commits. Use a maintainable design with explicit atomic state transitions; language and storage are implementation choices. Take shared task 1.
3. Builder hands the full committed revision, commands, limitations and complete stage-1 specification including runtime limits to the existing reviewer in this room. Reviewer takes shared task 2 and derives independent checks before inspecting implementation, then runs the isolated official harness and supplementary cases against that revision. No concurrent source writes during review. Reviewer owns only its evidence/tests and review report.
4. Genuine review defects return with expected/actual behavior and reproduction. Builder repairs in new commits. Reviewer rechecks relevant failures and the final isolated suite. Correct work may pass first review; do not manufacture disagreement.
5. Planner reports actual revision, results, evidence, remaining limits and independent readiness. Stop at stage 1. No human clarification or approval is requested during the run.

All room assignments and replies use literal participant mentions. Every delegated handoff includes the complete task and applicable specification text, not only a path or message reference. Use exact absolute paths; establish shared local access before relying on filesystem evidence, or supply inspectable safe artifacts.

## Acceptance map

Every row is an acceptance obligation. Test counts alone do not replace this map. Builder demonstrates focused behavior; reviewer independently chooses cases and records outcome per group with evidence paths.

| ID | Source | Required behavior and acceptance evidence |
|---|---|---|
| S01 | §§1–2 | HTTP API only; no later-stage features. Clean single-container build from stage-1 alone and RUN.md reproduction, with no parent files, submodules or symlinks. |
| S02 | §§2–3 | Image serves on 0.0.0.0, configurable PORT, default 8080. Ready health is 200 with status ok within 60 s. No runtime outbound dependency; all assets and time-zone data included. |
| S03 | §2 | Within 2 vCPU/2 GiB; up to 50 in-flight requests; normal requests within 5 s, test control within 10 s; no 5xx. Ephemeral state is permitted. Record observed timings and container constraints. |
| S04 | §§3–4 | Unauthenticated reset replaces every state element, returns empty 204, supports repeated resets, seeds users/restaurants/tables and confirmed reservations. After return, old credentials, sessions, receipts and occupancy are gone. |
| S05 | §§3–5 | JSON UTF-8 contract, explicit-offset RFC3339 responses, opaque IDs at most 64 characters including fixture IDs; unknown body fields/query parameters ignored. |
| S06 | §4 | Arbitrary calendar dates including past booking starts; no blanket future-only restriction. Fixture opening hours are local, weekday-specific, same-day; missing day closed. Seeded logins work immediately. |
| E01 | §5 | All 4xx/5xx carry error.code and human-readable message. Malformed JSON/wrong ordinary body type 400 malformed_request; missing required or invalid-format/range fields 422 validation_failed. |
| E02 | §5 | Endpoint exceptions: invalid party_size, including string/bool, gives 422; malformed local date-time strings give 422. Decimal query syntax rejects exponent, decimal point and plus sign. |
| A01 | §6 | Signup 201; login 200; correct user_id/display_name/token shape. Duplicate email 409 email_taken; short password and invalid email 422; wrong/unknown login 401. |
| A02 | §6 | Passwords use a proper password hash, never plaintext. Multiple tokens/sessions coexist without expiry. Missing/malformed/unknown bearer token 401 on protected endpoints. |
| A03 | §§6,8,10 | Health, reset, auth, restaurant list/detail, availability, export/import are public. Reservation reads/mutations and moves require auth; another owner's booking is 404, without existence leakage. |
| I01 | §7 | Create and moves require nonempty key: absent/empty 400 missing_idempotency_key; more than 255 chars 422. Scope by authenticated user, method and path. Same key across users/paths is independent. |
| I02 | §7 | Same parsed JSON value ignores whitespace/key ordering. Replay returns 200 and exactly original response; one first success 201. Different body for used key 409 idempotency_key_reuse. |
| I03 | §7 | After object parsing and authentication, resolve used keys before field validation/resource checks. Failed 4xx consumes no key. Unknown ignored fields still participate in full-body equality. |
| I04 | §§1,7 | Concurrent identical creates/moves produce exactly one 201, other 200s with identical receipt; never duplicate operations. Replay after amendment/cancellation remains original, with no new state change. |
| R01 | §8 | Public restaurant list has required fields; detail matches fixture configuration/order and unknown restaurant is 404. No creation endpoints. |
| V01 | §8 | Availability requires restaurant_id/date/party_size, validates inputs, local date, returns timezone. Slots advance by grid from opening; end fits closing. Closed day empty. |
| V02 | §§1,8 | Capacity filter and confirmed half-open occupancy determine available IDs in fixture order; full slots remain with empty arrays; cancelled reservations do not occupy. Adjacent bookings may coexist. |
| B01 | §8 | Create returns all specified fields, confirmed status, unique 6–12 A–Z0–9 reference, stable IDs, local time, offset times, correct end and creation time. |
| B02 | §8 | Conflict 409 table_unavailable; off-grid 422 not_on_slot_grid; outside/open-close overflow 422 outside_opening_hours; capacity 422 party_exceeds_capacity; invalid party 422 validation_failed; unknown/wrong-restaurant table 404. |
| B03 | §§1,8 | Concurrent conflicting create/amend/move operations never double-book or partially commit. Rejected operations preserve data/occupancy/receipts. Include 50 in-flight contention. |
| B04 | §8 | Caller list includes confirmed and cancelled, sorted by start instant descending; empty list shape correct. Reference lookup returns same reservation shape and only own records. |
| C01 | §8 | Cancellation frees table immediately and returns current state; repeated cancellation succeeds even after cutoff. At/after cutoff 409 cutoff_passed for an active reservation. |
| P01 | §8 | PATCH accepts any subset, retains omitted fields, same create validation, no key needed, cutoff measured against current start. Cancelled gives 409 reservation_cancelled. Failed amendment preserves old booking/occupancy. |
| P02 | §8 | Successful amendment releases old and acquires new occupancy atomically; reference/reservation_id/owner/creation time remain stable. No-op retains values. |
| T01 | §9 | IANA offsets and DST for Berlin 2026-03-29/10-25 and New York 2026-03-08/11-01. Spring gap omitted in availability and booking rejected with 422 invalid_local_time. |
| T02 | §9 | Fall repeated local time appears once, selects first occurrence; second cannot be selected. Duration measured in absolute elapsed minutes, using UTC arithmetic across transitions. |
| X01 | §10 | Public export 200 object: track tablekeeper, format_version 1, opaque state object; atomic read-only snapshot unaffected by later source writes. |
| X02 | §10 | Import unchanged export into independent process/container with no source connection; replaces destination atomically, 204; repeated import does not duplicate. Invalid envelope/state 422 and malformed JSON per §5, preserving destination. |
| X03 | §10 | Preserve accounts/hashes/logins, every existing token, fixture order/configuration, reservations/status/identity/reference/timestamps, successful request bodies and original receipts; failed keys stay reusable. Remove prior destination data and credentials. |
| X04 | §10 | Reset clears imported state; snapshots from before subsequent source changes remain stable; receipt replays after import of changed/cancelled bookings remain original. Do not commit exports. |
| M01 | §11 | Moves needs bearer and key; 1–8 objects with distinct string references. Invalid shape/duplicates 422, unknown/other owner 404, mixed restaurants 422. |
| M02 | §11 | Each move accepts PATCH fields, omitted retained, unknown ignored; stable identity/owner/creation time; cancelled 409; each old cutoff applies. |
| M03 | §11 | Non-occupancy errors in input order; cutoff before other changes for that booking. Check all non-occupancy errors before resulting occupancy conflicts. |
| M04 | §11 | Swaps/cycles evaluate all resulting bookings together; resulting overlaps with listed or unlisted booking 409. Unchanged listed booking still occupies its table. All-or-nothing reservation/occupancy/key commit. |
| M05 | §§7,11 | Successful moves 201 reservations in input order including unchanged; exact 200 receipt replay after later modifications; full no-op preserves all values. Export/import preserves batch receipts. |
| F01 | Guide | Three generic mandates retained, real builder/reviewer room exchange and commit history, full-spec handoffs, actual evidence and timings; no false spend estimate or manufactured review disagreement. |
| F02 | Guide | Final official harness isolated run against exact committed revision, fresh evidence directory, stage-1 results and stage-2 overshoot probe distinguished. No skipped/empty/startup-error suite counted as pass. |

## Specification interpretations

- Section 10 explicitly exempts export/import from auth despite the earlier general auth list, and grants test control calls a 10-second timeout.
- Endpoint-specific error rules override general type rules, particularly party_size and the moves array shape. Used-key comparison happens before fresh endpoint validation.
- Idempotency scope includes method/path as explicitly required; comparison uses the entire parsed JSON body, although unknown fields have no endpoint effect. JSON booleans are not numbers.
- Grid enumeration is local wall-clock from opening; existence/first-occurrence resolution uses IANA rules. Duration and overlap comparisons use real instants, including the closing instant. Test both transitions and the half-open interval boundary.
- Cancellation cutoff includes equality; already-cancelled repeat remains successful. Amendments/moves use the old start, preventing escape by moving a too-late booking to the future.
- The next-stage suite is only the official overshoot probe, not permission to add stage-2 capabilities. A failed probe is expected for stage 1.
- Final stage readiness concerns this local independently verified API. Room download, event submission, presentation/video and official acceptance are not claimed or performed by this run.
- Table IDs belong to each restaurant's catalogue; identical table IDs in different restaurants are valid. Occupancy is scoped to the restaurant/table pair. The initial extra global-uniqueness restriction was rejected and repaired.
- Accepted opaque fixture IDs remain addressable through percent-encoded path segments. Select the route before decoding its resource ID once, preserving public detail 200/404 and protected-route authentication. The initial full-path decoding defect was rejected and repaired.

## Recorded completion evidence

Builder produced the API and focused checks; Reviewer independently authored and ran checks and issued two concrete rejections before the final passing revision. Planner supplied reproducible atomicity and opaque-ID candidates and assessed the returned evidence. The complete repair history and original failures remain preserved.

- Final API commit: `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8`; stage tree `0050accbdc6d0457ffdc73de6365158e65c1808b`.
- Official isolated evidence: `reviewer-official-05/harness/report.json`, 120/120, zero failures/errors/skips/deselections.
- Independent evidence: `reviewer-independent-09/independent.log`, 27/27, 955 requests, no 5xx, normal/control maxima 3.351785 s / 0.121121 s.
- Review coverage: `reviewer-coverage-notes.md`; rejection history: `reviewer-rejection-01.md` and `reviewer-rejection-02.md`.
- All evidence paths are relative to `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1`.
- Source specifications/tests and generic mandates are unchanged. Stage 2 remains outside this run.

## Reproducible official check

Run from the authoritative checkout with a new output directory on each attempt:

```sh
PATH="/Applications/Docker.app/Contents/Resources/bin:/Users/athvs/.cache/figueira-band-harness/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 /Users/athvs/.cache/figueira-band-harness/bin/python -m harness run --track tablekeeper --repo '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper' --stage 1 --mode isolated --out '/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/official-stage-1/UNIQUE-RUN'
```

The reviewer records full tested commit, image/build evidence, command, observed suite counts/exit statuses, timings, supplementary cases, remaining gaps and explicit acceptance/rejection. The final report must not equate a shipped-check claim with official acceptance.
