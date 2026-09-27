# Requirement interpretation and acceptance boundaries

These decisions derive from the supplied official specifications. They do not add product requirements to the generic mandates. A later stage adds the stated behavior to an accepted copy; it never changes an earlier accepted folder.

## Cross-stage rules

- The participant guide's graded-track next-stage probe applies at every boundary below stage 4. The toy-only exception in the walkthrough does not apply to Tablekeeper.
- A supplied-test pass is partial evidence. The guide's scoring threshold does not authorize accepting a known specification defect.
- Build network access and offline runtime are different: dependencies may be fetched during the image build where allowed, while service operation and all browser assets must work without outbound access.
- Unknown request fields are ignored by domain validation but remain part of the full parsed JSON value used to compare idempotent requests. Retrying through a second token for the same account must use the same account/method/path/key namespace.
- Original successful receipts are immutable snapshots. Current resource changes, migration, cancellation, policy publication or plan application cannot rewrite them.
- A batch validates its complete resulting arrangement and commits once. It must not reserve targets one member at a time, expose a partial move or consume a key after rejection.
- Stage folders are separate build contexts. No sibling-stage or host-source imports are permitted. No restart persistence or external service is implied by the specification.

## Stage 1

The product is API only. Past starts remain valid. Cutoff is measured against the current start; it cannot be escaped by proposing a later one. Duration, overlap and cutoff use absolute instants. The wall-clock grid is anchored to opening, gaps are absent, and ambiguous starts use the first occurrence. Explicit endpoint-specific errors override generic wrong-type rules. Arbitrary multi-fault precedence is not invented where the specification does not state one.

## Stage 2

Available singles remain in fixture order, followed by explicitly declared pairs in declared order. A pair is a set for identity and occupancy; reversed input is not a different seating choice. Combining is not transitive. API IDs are opaque; UI presentation uses human-readable names and table labels.

The browser must track the initiating search, selection, form body, user and route for in-flight work. Late success, failure or cleanup from a superseded operation cannot overwrite newer intent. A network-uncertain booking preserves its exact retry body/key; confirmed rejection and uncertain outcome are distinct visible states. Refreshing availability after rejection preserves the selected form and user inputs. Repeated unchanged successful submission resolves the original receipt without another booking. Changing a field creates a new request identity.

Upgrade tests preserve an existing browser session and pending retry across import between requests. They do not invent a requirement for migration halfway through a single HTTP request, background polling or cross-tab synchronization.

## Stage 3

Policy selection uses the resulting local start date, greatest applicable effective date and then greatest publication version for ties. Restaurant detail remains the original fixture, so the UI must not infer current availability from its static capacity/duration fields. Each accepted booking preserves its entire policy snapshot. Real changes validate all resulting fields against the applicable policy after the old accepted cutoff check; no-ops retain terms and history.

History/decision and series reads have the explicit unauthenticated 404 privacy rule. It supersedes the general authenticated-endpoint 401 rule for those reads only. Receipts from earlier-stage exports remain original JSON values, even when the current migrated representation gains fields. The implementation must not invent unavailable historical edits from older stages.

An adopted anchor retains its identity and record. Occurrences have independent identities, scheduled local dates and exceptions. Individual real changes permanently mark exceptions; cancellation keeps an occurrence without creating an exception. Collective real changes increment each affected series once, and the restaurant once per whole operation.

## Stage 4

A preview may store a plan but must not store a closure or change occupancy, history or revisions. Plan assignment uses each booking's accepted capacities and preserves its accepted time/terms. Considered bookings are selected by overlap with the proposed closure; candidate assignments must still be checked for the booking's entire interval against fixed bookings and previous closures.

The deterministic objective is lexicographic: changed-booking count, total unused seats, then option-rank vector in reservation-reference order. A feasible plan that is merely convenient is insufficient. Atomic application records closure and seating changes together; intervening restaurant changes invalidate it, while unrelated restaurants do not.

Recurring amendments use original scheduled dates and current seating, exclude cancelled/permanent exceptions, retain terms for no-ops, and use expected series revision before occurrence cutoff/booking validation. Operator seating repairs preserve exception flags and accepted terms. No new manager or recurring-management screen is required; the existing diner interface must reflect authoritative applied state when it reads it.

## Evidence limitations

The authentic room export is supplied by the operator after completion. Missing `room.json` must remain an explicit offline-check limitation. Provider monetary spend is unmeasured unless a verified runtime source supplies it. Scenario plans, distinct cases, repeated scenario executions and raw HTTP-request counts must be reported separately.
