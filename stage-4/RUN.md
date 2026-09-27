# Tablekeeper · Stage 4

From this folder, build and start the standalone browser product and JSON API:

```sh
docker build -t tablekeeper-stage4 . && docker run --rm --name tablekeeper-stage4 -e PORT=8080 -p 8080:8080 tablekeeper-stage4
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
account, session, reservation, policy, history, series, plan, closure and receipt. `GET /restaurants`, restaurant detail
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
in the past are valid. Cancellation/amendment cutoffs use the accepted terms and
the booking's current start.

## Policies, decisions and history

Fixture restaurants may supply `manager_user_ids` (default empty). Only those
accounts may `POST /restaurants/{id}/policies`, with an idempotency key and a
complete policy: effective date, grid, duration, cutoff, hours and every table's
capacity. Grid/duration are 1–1440, cutoff 0–10080, and published capacities 1–100.
`GET /restaurants/{id}/policies` is public and lists immutable publications in
version order. The original restaurant detail never changes. For each local
start date, the latest eligible effective date wins; publication version breaks
ties. Policy zero is the fixture configuration.

Live reservations carry `revision` and complete `accepted_terms`. A real change
checks the old accepted cutoff and then validates every resulting field under
the resulting date's selected policy. It replaces terms/end time and increments
revision once. No-op amendments retain those values but still require an editable,
confirmed booking. Optional positive `expected_revision` rejects a stale change
before cutoff or field validation. Cancellation increments once; repeated cancel
does not. Atomic moves apply these same rules to all items before any commit.

`GET /availability?...&explain=true` adds both independent capacity and overlap
rules for every table in fixture order, including the selected policy version.
The parameter's only accepted value is `true`; omission adds no explanations.
The browser takes displayed seating capacities from authoritative availability
and cancellation terms from the actual receipt/record, never static fixture rules.

`GET /reservations/{reference}/history` returns immutable ordered events with
contiguous sequence numbers, resulting revision/terms and actual field changes.
`GET /reservations/{reference}/decision` returns current revision/terms. Both
return 404 for anyone except the owner, including callers without a token.
Pair histories use canonical complete member lists; single-to-single changes
keep `table_id`. Replays, failures, no-ops and publication append no events.

## Recurring agreements

`POST /series` requires an idempotency key and an owned, confirmed, editable
`anchor_reference`, `count` 2–12 and `interval_weeks` 1–4. It retains the anchor
unchanged and prepares each following occurrence by local calendar weeks, using
that date's policy and IANA rules. The first failing index, including occupancy,
rejects the entire adoption. No records, histories, counters or retry claim remain.

`GET /series/{series_id}` returns current occurrences in fixed index order; only
the owner can read it, with 404 for other or unauthenticated callers. A real
individual change permanently marks an exception and increments series revision.
Cancel increments revision without creating an exception or cancelling siblings.
A collective move increments each affected series once, even when several of its
occurrences change. Restaurant revisions are exposed by closure previews; adoption and a real batch
increment once per operation. No policy, history or series UI screen is required.

## Closure plans and collective series amendments

Managers can `POST /restaurants/{id}/replans` with a table and explicit-offset
`from`/`to` instants, then `POST /restaurants/{id}/replans/{plan_id}/apply` with
`{}`. Both require idempotency keys. Preview considers all confirmed overlapping
bookings and solves the exact objective: fewest changed table sets, then least
unused capacity, then the option-rank vector in reference order. Each booking
uses its own accepted capacities and full interval. Fixed bookings, prior
closures and the proposed closure constrain every member of an option. The
bounded solver supports six tables, four pairs and six considered bookings;
larger requests return `planning_limit` without mutation.

Previews store only plans and receipts. Apply checks the captured restaurant
revision and commits the closure with every seating assignment in one transaction.
Even an empty plan increments the restaurant revision once. Moved records gain
one revision and a `reassigned` event with complete `table_ids` and `plan_id`;
terms, times, identity and diner exception flags survive. Each affected series
increments once. Successful-key retries remain original receipts, while an
already-applied plan with a different key is refused. Closures participate in
all availability, explanation, booking and amendment occupancy decisions.

Owners can `POST /series/{id}/amend` with an idempotency key, positive
`expected_revision`, valid `from_index` and exact `local_time` HH:MM. Eligible
nonexception, confirmed occurrences keep their original scheduled dates and
current seating. All real changes validate old cutoff and the resulting policy
before collective occupancy checking. No-op or empty eligible sets succeed even
after an occurrence's cutoff, retaining terms and all counters. A real operation
increments changed bookings and the series/restaurant once, without creating
exceptions. Failures commit nothing. Original schedules are saved at adoption;
for stage-3 imports they are recovered from the immutable adoption receipt,
not inferred from an amended anchor. Portable snapshots preserve plans,
closures, schedules, reassignment histories and every old or new receipt.

The existing browser lookup and explicit availability search read current seating
and closures. An unchanged booking retry displays its original confirmation
receipt; idle confirmations do not poll for operator changes.

## Portable state

`GET /_test/export` returns a JSON snapshot with track `tablekeeper`, version 1 and
opaque state. `POST /_test/import` accepts that entire object unchanged and
atomically replaces all state. It preserves hashes, sessions, identities,
timestamps, references, current records and original retry receipts. Invalid
snapshots leave existing state intact. Stage-1, stage-2 and stage-3 exports from this team
import unchanged: tokens and identities survive; live records gain policy-zero
terms and revision 1 while retaining their original occupancy. Original receipt
bodies/responses keep their exact old JSON shape. Earlier stages did not record
history, so imported history starts empty; subsequent real events begin at seq 1
without inventing pre-upgrade edits. A cancelled reset seed similarly has no
invented cancellation event, starts at revision 1 and has empty history. A confirmed
reset seed gets a creation event at initialization. Stage-3 snapshots preserve all
actual events, publications, series membership/exceptions and original receipts.
These unauthenticated test controls are
enabled in the image by contract. Export files contain credentials/session tokens
and must be kept private.

## Browser recovery and identity

The browser uses actual API responses for browsing, booking and lookup/cancellation.
Its local JSON codec reads integer tokens as BigInt and retains other decimal
tokens without binary-float conversion. Guest input is validated from its exact
decimal spelling, query counts use plain digits, and JSON request counts remain
unquoted numbers. Capacity sums, displayed counts and retained retry bodies do
not acquire a JavaScript safe-integer ceiling or silently round adjacent values.
An available time opens a form that remains visible after booking. Unchanged
submissions reuse their original body/key and contact the service again; changing
the selection or guest count creates a new intent. A confirmed rejection displays
an error; a connection failure displays uncertainty and preserves the exact retry.
Confirmed refusals refresh availability while keeping the selected form and edited
inputs, including when a policy changed after the diner chose a time.

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
restart durability requirement. Closures and agreements remain API workflows; no administrative screens are required. All four existing browser routes remain available.
