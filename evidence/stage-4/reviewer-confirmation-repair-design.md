# Confirmation repair regression design

Written after the original candidate rejection and before inspecting any repaired source.

Retain the independent group 15 single/pair test: explicitly await successful unchanged replay, require original response JSON exactly, then require current server seating on both confirmation fields. Re-run all inherited browser flows, including uncertain POST outcomes and same-key upgrade recovery.

Add two bounded regressions for the newly introduced detail-read boundary:

1. Abort the authenticated current-reservation GET after a known successful booking POST. The success reference must remain available, and the UI must not report booking refusal or uncertainty about that already acknowledged POST. The unchanged retry must use the same key/body and produce exactly one reservation. Preserve a rendered screenshot for human assessment of the detail-refresh message.
2. Delay the current-reservation GET, select different available seating, then release the older detail response. It must not overwrite the new selection or add an old confirmation to the new form. This extends the inherited rule that late responses must not restore stale booking state.

These cases exercise the proposed read boundary, not a prescribed implementation structure. No implementation was copied into the tests. If the chosen repair exposes another genuine user-driven authoritative refresh mechanism, assess the same semantic conditions without requiring a particular private helper or arbitrary new test ID.
