# Tablekeeper — Stage 1

From this directory, build and run a single container:

```sh
docker build -t tablekeeper-stage-1 .
docker run --rm --name tablekeeper-stage-1 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper-stage-1
```

`GET http://localhost:8080/health` returns `{"status":"ok"}`. There is no manual setup. The service starts with empty state; load any Stage 1 fixture with `POST /_test/reset`. To choose a different port, set `PORT` and map that container port (for example `-e PORT=8090 -p 8090:8090`). The default is 8080, bound on `0.0.0.0`.

Python 3.12, its standard library and the Debian image's IANA timezone database are the complete runtime. There are no pip dependencies, external services, startup downloads or parent-directory files. Docker may download the base image at build time; runtime needs no outbound connectivity. The process runs as an unprivileged user. Disk persistence is intentionally unnecessary.

## Design and behavior

- A threaded HTTP server admits 50 concurrent requests; one process-wide reentrant lock serializes state transactions. Mutations run against a detached candidate state; only successful dispatch and response encoding publish it. Exceptions restore the previous state. Reads and exports use the same lock, with immutable encoded responses prepared before unlocking. A successful mutation and its retry receipt become visible together.
- Reservations occupy half-open UTC intervals, scoped by restaurant ID plus table ID; separate restaurants may reuse their local table IDs. Opening grids use local wall time, with `zoneinfo` first-fold resolution and round-trip gap detection. Ends are calculated using absolute elapsed time.
- Batch amendments validate every non-occupancy rule first, then test the complete candidate state before replacing any records. PATCH and cancellation use the current booking's cutoff.
- Full parsed request bodies are stored with successful receipts, scoped by user, method, path and key. Booleans differ from JSON numbers; numeric spellings with equal value compare equally. Failed requests store no receipt.
- Copying, equality and encoding of JSON trees use explicit stacks, and deep decoding falls back to an explicit container stack using the standard library's scalar parser. Deep ignored fields remain part of receipt equality and portable snapshots without depending on the Python call-stack limit.
- Accounts use salted scrypt hashes (N=16384, r=8, p=1). Sessions have random 256-bit bearer tokens and remain valid until reset/import replacement.
- Export contains versioned, implementation-defined JSON. Import validates its structure, links, hashes, times, occupancy and receipts in detached memory, then atomically replaces state. Export/import need no source process or filesystem.

The API surface is exactly Stage 1: public health, restaurant browsing, availability, signup/login and test controls; authenticated reservation creation/list/lookup/cancellation/amendment and atomic moves. Errors are JSON envelopes with the specification's status/code. Unknown body/query fields have no endpoint effect, but body fields still affect idempotency equality.

## Focused checks

With Python 3.12 or newer, `python -B -m unittest -v test_contract` starts two temporary independent service processes and runs 21 test groups. They cover 50 concurrent creates/moves/logins, full-body retries, rollback, both specified zones' DST transitions, ownership, import replacement, retained receipts and validation. Repair regressions cover restaurant-local table IDs, fixture numeric error codes, deep ignored JSON in both writes and portable receipts, injected transaction/encoding failures, and public addressing of opaque restaurant IDs. Route segments are recognized before decoding each ID exactly once, preserving slashes, Unicode and literal percent escapes. To test already-running containers instead, supply `TABLEKEEPER_URL` and `TABLEKEEPER_SECOND_URL`. The fault-injection group still checks the local transaction engine. Test accounts are synthetic and exports remain in memory. These checks supplement independent review and the official harness; they do not claim official acceptance.

Test endpoints are deliberately enabled and unauthenticated as required. Exports contain hashes and live sessions: keep them private and never commit them. Application logging excludes bodies and authorization headers. State is ephemeral and is lost when the process exits. There is no UI or later-stage implementation.
