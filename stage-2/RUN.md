# Tablekeeper — Stage 2

From this directory, build and start the complete service:

```sh
docker build -t tablekeeper-stage-2 .
docker run --rm --name tablekeeper-stage-2 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper-stage-2
```

Open http://localhost:8080 for restaurant search and booking. `/signup`, `/login` and `/lookup` are directly addressable screens. `GET /health` returns `{"status":"ok"}`. No manual setup is required. State starts empty; `POST /_test/reset` loads the supplied fixture shape, including optional declared table pairs and cancelled reservations. Restaurants come only from fixtures. The default listening address is `0.0.0.0:8080`; another port works with, for example, `-e PORT=8090 -p 8090:8090`.

The image includes Python 3.12, standard-library modules, IANA timezone data and Liberation fonts with their license. Fonts are installed during the Docker build and served from this container alongside HTML, CSS and JavaScript. There are no pip packages, sibling-folder dependencies, external runtime services or startup downloads. The process runs as an unprivileged user. No runtime outbound connection is needed; disk persistence is intentionally unnecessary.

## State and concurrency

A threaded HTTP server admits 50 concurrent requests. One process-wide reentrant lock serializes transactions. Mutations use a detached candidate state; only successful dispatch and response encoding publish it. Exceptions restore the previous state. Reads and exports share the lock, preparing immutable encoded responses before unlocking. A mutation and its successful retry receipt become visible together.

Occupancy is a half-open UTC interval on every selected table, scoped by restaurant. Declared pairs canonicalize to fixture order, consume both members, and use their summed capacity. Atomic moves validate all non-occupancy rules before checking the complete resulting allocation. Local grids use `zoneinfo`, first-fold resolution and gap detection; durations use absolute elapsed time. These are inherited Stage 1 semantics.

Receipts retain entire parsed request bodies, including ignored fields, scoped by user, method, path and key. JSON numbers compare by numeric value and differ from booleans. Explicit-stack copying, equality, encoding and deep decoding preserve nested bodies without relying on Python recursion depth. Failed requests consume no keys. Passwords use salted scrypt (N=16384, r=8, p=1); random bearer sessions remain valid until reset or import replacement.

Exports are atomic, versioned JSON snapshots. Import validates configuration, identities, hashes, times, occupancy and receipts before replacement. Unchanged exports from this service and the accepted Stage 1 service work in an independent process. Legacy validation lives in `legacy_model.py`; migration adds table sets to current records without modifying original retry responses or session tokens.

## Browser behavior

The interface uses locally served typography and assets, visible labels and keyboard focus, responsive seating cards and distinct availability, selection, loading, confirmation, refusal and uncertainty states. Search generations prevent an older response from replacing a newer restaurant, labels or form.

Booking forms retain their full request and idempotency key for unchanged retries. Every retry reaches the server. A lost response shows uncertainty; a confirmed conflict shows refusal and refreshes availability while retaining the form. A changed field creates a new request identity. Successful confirmation keeps the form available. Browser sessions use local storage, allowing existing sessions and open pending forms to continue through an import between requests. Lookup displays the current owner-visible reservation and supports cancellation.

## Focused checks

With Python 3.12+, run inherited API checks using:

```sh
python -B -m unittest -v test_contract
```

This starts two temporary independent service processes and runs 21 groups covering contention, moves, DST, idempotency, privacy, replacement imports, deep ignored JSON and transaction rollback. For existing containers set `TABLEKEEPER_URL` and `TABLEKEEPER_SECOND_URL` instead. The injection test checks the local transaction boundary directly.

The seven additional groups in `test_stage2.py` exercise pair validation/occupancy/moves/import, 50-way pair/single contention, browser races, post-commit response loss, stale selection, real Stage 1 migration with the same open browser form, lookup and a 375px layout. They require Playwright Chromium, two running Stage 2 services, a running Stage 1 service and an evidence directory:

```sh
TABLEKEEPER_URL=http://localhost:8080 \
TABLEKEEPER_SECOND_URL=http://localhost:8081 \
TABLEKEEPER_STAGE1_URL=http://localhost:8082 \
BUILDER_EVIDENCE=/absolute/path/to/new-evidence \
python -B -m unittest -v test_contract test_stage2
```

Tests use synthetic identities and retain tokens and snapshots only in memory. Their output supplements the independent review and cumulative isolated harness; it does not establish official event acceptance.

Test controls are intentionally unauthenticated. Exports contain hashes and live sessions and must stay private. Logging excludes request bodies and authorization headers. State is lost when the process exits. This folder implements Stage 2 only; policy publication, history, recurring agreements and closure planning belong to later folders.
