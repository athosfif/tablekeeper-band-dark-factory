# Tablekeeper · Stage 2

From this folder, build and start the standalone browser product and JSON API:

```sh
docker build -t tablekeeper-stage2 . && docker run --rm --name tablekeeper-stage2 -e PORT=8080 -p 8080:8080 tablekeeper-stage2
```

Readiness: `curl http://localhost:8080/health`. Change both the environment variable
and the container side of the mapping to use another port, for example
`-e PORT=9090 -p 9090:9090`. PORT defaults to 8080; the server binds to 0.0.0.0.

Python 3.12 and the local IANA timezone database are included in the image. There
are no pip packages, external services, volumes, outbound runtime requests or
manual initialization steps. The process runs as an unprivileged user. Visit
`http://localhost:8080/` to use the browser product. State is initially empty and
deliberately ephemeral; the page explains when no restaurants are configured.
The `/`, `/signup`, `/login` and `/lookup` routes return HTML. Scripts, styles,
illustrations and icons are included locally; typography uses system fonts.

## API and fixture setup

`POST /_test/reset` with the specified JSON fixture supplies users, restaurants,
tables and optional confirmed reservations. It returns 204 and replaces every
account, session, reservation and receipt. `GET /restaurants`, restaurant detail
and `GET /availability?restaurant_id=...&date=YYYY-MM-DD&party_size=...` are public.
`POST /auth/signup` and `POST /auth/login` issue independent, non-expiring bearer
tokens. Passwords are salted scrypt hashes, including fixture passwords.

Authenticated routes are `POST /reservations`, `GET /reservations`,
`GET /reservations/{reference}`, `PATCH /reservations/{reference}`,
`POST /reservations/{reference}/cancel` and `POST /reservation-moves`.
The two creation routes require an `Idempotency-Key` of 1–255 characters.
Only the initiating user can read or mutate a booking. Unknown fields are ignored
for behavior, but remain part of the parsed JSON body used for retry comparison.

## Consistency and time

Restaurants may declare unordered pairs through `combinable`. Availability keeps
single-table IDs and adds all eligible singles followed by declared pairs in
fixture/declaration order. A pair occupies both members for its whole interval.
Creates, amendments, seeds and atomic moves accept `table_ids`; legacy `table_id`
requests remain supported. Current records include `table_ids`, plus `table_id`
only for a singleton. Cancelled seeds retain their status and do not occupy seats.

A threaded HTTP adapter feeds one in-memory transactional store. A single lock
serializes state reads, validation and writes. Candidate changes are checked in
full before commit, so a swap has no intermediate occupancy. Snapshot reads and
state replacement use the same boundary. Responses are detached copies before
the lock is released; network delivery never holds a transaction open.

Successful writes store the full original response separately from current
records. The retry namespace includes user, method, path and key. Replays return
the original receipt, including after amendment/cancellation. Failed requests do
not reserve a key. Same JSON numbers compare numerically, object order is ignored,
and array order and Boolean types remain significant. Decimal JSON numbers retain
their precision and exponent in ignored fields, receipts and portable snapshots.

Slot grids use local wall-clock minutes from opening. IANA conversion rejects
nonexistent local times and uses the first occurrence of a repeated time. Duration,
overlap and cutoff comparisons use UTC instants; intervals are half-open. Starts
in the past are valid. Cancellation/amendment cutoffs use the current start.

## Portable state

`GET /_test/export` returns a JSON snapshot with track `tablekeeper`, version 1 and
opaque state. `POST /_test/import` accepts that entire object unchanged and
atomically replaces all state. It preserves hashes, sessions, identities,
timestamps, references, current records and original retry receipts. Invalid
snapshots leave existing state intact. Stage-1 exports from this team import
unchanged: existing tokens and identities survive, current single-table records
gain the stage-2 representation, and original stage-1 receipt bodies/responses
remain untouched. These unauthenticated test controls are
enabled in the image by contract. Export files contain credentials/session tokens
and must be kept private.

## Browser recovery and identity

The browser uses actual API responses for browsing, booking and lookup/cancellation.
An available time opens a form that remains visible after booking. Unchanged
submissions reuse their original body/key and contact the service again; changing
the selection or guest count creates a new intent. A confirmed rejection displays
an error; a connection failure displays uncertainty and preserves the exact retry.
Conflicts refresh availability while keeping the selected form and edited inputs.

Asynchronous search, authentication, booking, lookup and cancellation callbacks
check their initiating route, session and interaction generation before changing
the DOM. An older completion cannot replace a later search/selection, sign in a
different account, display someone else's confirmation, or clear newer work.
The session token/display name persist locally for direct route navigation;
pending requests live in the page. A compatible legacy single-table client can
retain that session and pending form across an import between requests, including
recovering a lost stage-1 confirmation. No polling, cross-tab synchronization or
pending-operation recovery after page reload is implemented or required.

## Operational scope

The container supports the required 2 CPU / 2 GiB deployment. The lock favors
simple, auditable serializability over multi-process throughput. Run one process
per service: separate replicas do not share this ephemeral store. There is no
restart durability requirement. There are no policies, revisions, recurring
agreements, closures or other stage-3/4 features in this folder.
