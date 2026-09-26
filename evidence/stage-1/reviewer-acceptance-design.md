# Independent stage-1 acceptance design

Derived 2026-09-26 from the complete official specification at `803560d2a678ace1414465c098eb0ab5380ffade`, before reading implementation or shipped test source. Reviewer has read the active plan and verified the output repository's plan commit `5fd9d6898dfcefe7d71ea7b973f0c90ca91d76b9` is locally readable.

Only the HTTP interface is exercised. Test inputs use synthetic identities. Export payloads and tokens remain in test process memory, never logs or committed artifacts. Source is owned by Builder. Test failures must distinguish faulty test assumptions from service defects.

| Specification | Independent acceptance cases |
|---|---|
| 1 | Half-open adjacent intervals; 50 contenders with unique and identical keys; concurrent moves/amendments cannot overlap; reject atomically. |
| 2 | Build stage folder alone per RUN.md; two independent processes on an internal Docker network; inspect 2 CPU/2 GiB limits and health timing; overridden and default PORT; record per-request maxima. |
| 3 | Public health/reset, JSON charset, explicit offsets, repeated reset, supplied 64-character IDs, unknown fields/query parameters. |
| 4 | Fixture configuration/order, seeded reservations/users, past/leap dates, local weekday closure, capacity and grid independent of current date. |
| 5 | Malformed JSON/object/ordinary wrong types, required fields, endpoint party-size exceptions, date grammar, plain query integers, key bounds, machine and human error envelope. |
| 6 | Signup/login, duplicate email, 8-character password boundary, malformed credentials, concurrent tokens, hash inspection after checks, protected routes and ownership privacy. |
| 7 | Whole parsed JSON (nested unknown fields, order, whitespace, bool versus number), user/path scope, unauthenticated and invalid object before receipt; receipt before field/resource validation; failed key reuse; replay before and after resource mutations; concurrent one-201 rest-200. Method separation inspected because only POST is an idempotent Stage-1 method. |
| 8 | Complete restaurant/availability shapes and ordering; all create errors; unique references/IDs, sorting by instant; cancellation release/repeat/cutoff; PATCH subset/no-op/rollback/stable identity/old cutoff. |
| 9 | Berlin and New York skipped/repeated hours; first fold offset; unique repeated slot; absolute 90-minute duration and closing boundary; gap excluded/rejected; second fold offset input invalid. |
| 10 | Unauthenticated atomic export; independent destination import; source changed after snapshot; original create and move receipts, tokens, hashes/login, identities/status/time/config order; destination credentials removed; malformed/invalid import rollback; repeat import; reset clears imported state. |
| 11 | 1..8 boundaries, duplicate/reference/shape errors, same restaurant, privacy, no-op values, 8-cycle, swap, unchanged listed occupancy, unlisted collisions, input-order non-occupancy precedence (including later invalid fields versus earlier collision), old cutoff priority, 50 concurrent batch retries, rollback and receipt survival. |

Exact cutoff equality is assessed with a synthetic booking in the current UTC minute and cutoff 0 (the check runs at or after the start), supplemented by implementation inspection; deterministic equality to a moving wall clock cannot be selected through this API. Finite concurrency trials supplement, not replace, inspection of the atomicity boundary.

The official isolated harness is run in a new directory for each revision and includes the required next-stage overshoot probe. A stage-2 failure is expected. No skipped, empty or startup-failed stage-1 suite counts as acceptance. Hidden official checks remain unavailable; local acceptance is not official event acceptance.
