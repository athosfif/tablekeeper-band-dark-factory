# Tablekeeper — Stage 4

From this directory, build and start the complete service:

```sh
docker build -t tablekeeper-stage-4 .
docker run --rm --name tablekeeper-stage-4 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper-stage-4
```

Open http://localhost:8080 for restaurant search and booking. `/signup`, `/login` and `/lookup` are directly addressable screens. `GET /health` returns `{"status":"ok"}`. No manual setup is required. State starts empty; `POST /_test/reset` loads the supplied fixture shape, including optional declared table pairs and cancelled reservations. Restaurants come only from fixtures. The default listening address is `0.0.0.0:8080`; another port works with, for example, `-e PORT=8090 -p 8090:8090`.

The image includes Python 3.12, standard-library modules, IANA timezone data and Liberation fonts with their license. Fonts are installed during the Docker build and served from this container alongside HTML, CSS and JavaScript. There are no pip packages, sibling-folder dependencies, external runtime services or startup downloads. The process runs as an unprivileged user. No runtime outbound connection is needed; disk persistence is intentionally unnecessary.

## State and concurrency

A threaded HTTP server admits 50 concurrent requests. One process-wide reentrant lock serializes transactions. Mutations use a detached candidate state; only successful dispatch and response encoding publish it. Exceptions restore the previous state. Reads and exports share the lock, preparing immutable encoded responses before unlocking. A mutation and its successful retry receipt become visible together.

Occupancy is a half-open UTC interval on every selected table, scoped by restaurant. Declared pairs canonicalize to fixture order, consume both members, and use their summed capacity. Atomic moves validate all non-occupancy rules before checking the complete resulting allocation. Local grids use `zoneinfo`, first-fold resolution and gap detection; durations use absolute elapsed time. These are inherited Stage 1 semantics.

Receipts retain entire parsed request bodies, including ignored fields, scoped by user, method, path and key. JSON numbers compare by numeric value and differ from booleans. Explicit-stack copying, equality, encoding and deep decoding preserve nested bodies without relying on Python recursion depth. Failed requests consume no keys. Passwords use salted scrypt (N=16384, r=8, p=1); random bearer sessions remain valid until reset or import replacement.

Exports are atomic, versioned JSON snapshots. Import validates configuration, identities, hashes, times, occupancy, policies, terms, histories, series links and receipts before replacement. Unchanged exports from this service and the accepted Stage 1 and Stage 2 services work in an independent process. Prior validators live in `legacy_model.py` and `stage2_model.py`. Migration adds current table sets, policy-0 terms, initial revisions and history without modifying original retry responses or session tokens. Imported existing reservations can be adopted into recurring agreements. Original exported identities and timestamps remain unchanged.

## Policies, histories and recurring agreements

Restaurant fixtures optionally declare `manager_user_ids`. Managers publish complete immutable dated policies with idempotency keys; public policy lists retain publication order. Booking and availability select the greatest effective date not later than the booking's local date, breaking ties by publication version. Restaurant detail retains the original configuration. Availability explanations report capacity and occupancy independently, in fixture order, only when `explain=true` is explicitly requested.

Each reservation snapshots its accepted terms and starts at revision 1. Real amendments check the old accepted cutoff and then validate all resulting fields under the selected policy, replacing terms and end time atomically. No-op amendments keep their original terms. Optional expected revisions prevent concurrent stale amendments. Histories record only creation, real changes and cancellation, with monotonic sequence/time and immutable resulting terms. History and decision endpoints return owner-private 404 even without a token.

`POST /series` adopts an owned editable anchor without modifying it, and creates 2–12 weekly occurrences at intervals of 1–4 weeks. Each generated date resolves its own policy and DST rules. A failure rolls back the whole candidate transaction, including receipts and histories. Real individual changes permanently mark exceptions; cancellation retains an occurrence and does not cancel siblings. Collective moves update affected reservation histories and aggregate each restaurant/series revision once. Series lookups expose current states, while retries preserve the original response.

## Closures and collective recurring amendments

Managers can preview a closure plan and apply it with a separate idempotent request. Preview considers every confirmed reservation overlapping the proposed half-open interval. A bounded exhaustive search supports six tables, four declared pairs and six considered bookings. It uses bit masks and precomputed interval conflicts, pruning only when an objective lower bound cannot improve the current best. It minimizes changed assignments, then unused accepted capacity, then fixture-option ranks in reference order. Fixed bookings and all previous closures constrain each booking's full interval. Larger inputs return `planning_limit`.

Preview stores only the plan and receipt. Apply checks the exact restaurant revision, then atomically records the closure and every assignment. Customer times, party sizes, accepted terms and identities remain unchanged, even past the diner cutoff. Only moved bookings gain a revision and `reassigned` history entry. Each affected series and the restaurant advance once; exceptions and scheduled dates stay intact. Successful replay precedes current plan/resource checks. Applied closures exclude all affected single/pair choices from availability and ordinary mutations.

Owners can amend eligible recurring occurrences from an index using a required expected series revision and local clock time. Original scheduled dates are retained, while cancelled occurrences and permanent diner exceptions are excluded. All real changes validate old cutoffs and applicable new policies before final occupancy validation. Revisions/history change together, once per affected booking and once per series/restaurant, without marking exceptions. Empty and all-no-op sets succeed without revision changes.

Stage 4 accepts unchanged exports from its own service and accepted Stages 1–3. Previews, applied closures, original receipts, histories and series remain portable across independent processes. Import validates the inherited graph, stored planning inputs/objective, assignments, closure links and new receipts before replacement. `planning.py` is the pure optimization module; `stage3_model.py` retains the earlier validator.

## Browser behavior

The interface uses locally served typography and assets, visible labels and keyboard focus, responsive seating cards and distinct availability, selection, loading, confirmation, refusal and uncertainty states. Search generations prevent an older response from replacing a newer restaurant, labels or form.

Booking forms retain their full request and idempotency key for unchanged retries. Every retry reaches the server. A lost response shows uncertainty; a confirmed conflict shows refusal and refreshes availability while retaining the form. A changed field creates a new request identity. Successful confirmation keeps the form available. Browser sessions use local storage, allowing existing sessions and open pending forms to continue through an import between requests. Lookup displays the current owner-visible reservation and supports cancellation.

## Focused checks

With Python 3.12+, run inherited API checks using:

```sh
python -B -m unittest -v test_contract
```

This starts two temporary independent service processes and runs 21 groups covering contention, moves, DST, idempotency, privacy, replacement imports, deep ignored JSON and transaction rollback. For existing containers set `TABLEKEEPER_URL` and `TABLEKEEPER_SECOND_URL` instead. The injection test checks the local transaction boundary directly.

The eight additional groups in `test_stage2.py` exercise pair validation/occupancy/moves/import, 50-way pair/single contention, browser races, post-commit response loss, stale selection, real Stage 1 migration with the same open browser form, lookup and a 375px layout including unrestricted long restaurant and table labels. They require Playwright Chromium, two running Stage 2 services, a running Stage 1 service and an evidence directory:

```sh
TABLEKEEPER_URL=http://localhost:8080 \
TABLEKEEPER_SECOND_URL=http://localhost:8081 \
TABLEKEEPER_STAGE1_URL=http://localhost:8082 \
BUILDER_EVIDENCE=/absolute/path/to/new-evidence \
python -B -m unittest -v test_contract test_stage2
```

Stage 3 adds eight groups in `test_stage3.py`, for 37 cumulative builder groups. They cover policy ordering/ties/type errors/permissions/receipts, independent explanations, immutable history/no-ops/pairs/privacy, 50 competing expected-revision changes, series policy selection/exceptions/atomic moves/cancellation, DST failure rollback and reusable keys, populated history/series import, and upgrades from actual Stage 1 and Stage 2 processes. To include these, run all three test modules and provide `TABLEKEEPER_STAGE2_URL` pointing to a separate accepted Stage 2 service. The first two main URLs should then point to Stage 3 services. All URLs refer to independent processes; the source and destination need no shared volume.

Tests use synthetic identities and retain tokens and snapshots only in memory. Their output supplements the independent review and cumulative isolated harness; it does not establish official event acceptance.

Stage 4 adds twelve groups in `test_stage4.py`, for 49 cumulative builder groups. A separate exhaustive product-enumeration oracle checks 18 seating scenarios; other cases cover accepted capacities under later policies, single-to-pair repair/import, fixed bookings and earlier closures over full intervals, maximum supported planning dimensions, half-open closure boundaries, 50 identical plan applications and 50 competing series changes, stale/no-op/other-restaurant revisions, past-cutoff repairs, exceptions/cancelled occurrences, rollback, portable previews/applied histories/receipts and actual populated Stage 3 upgrades. Include all four test modules and set `TABLEKEEPER_STAGE3_URL` to an accepted Stage 3 service, with main source/destination URLs pointing to Stage 4. The inherited upgrade tests still use separate Stage 1 and Stage 2 URLs.

Test controls are intentionally unauthenticated. Exports contain hashes and live sessions and must stay private. Logging excludes request bodies and authorization headers. State is lost when the process exits. This folder is the complete cumulative Stage 4 service. Management operations are API-only; existing booking and lookup screens always read current server state.
