# Stage 2 acceptance ledger

Status: implementation assigned; no stage-2 product acceptance or executed-stage-2 pass is claimed.

## Committed candidate and Builder evidence

The complete candidate is `97031312f2ddd12b118388b369fcce576827ba43`, stage-2 tree `a0a23761dd71132ffe6c8b8cae29e2407d7e4517`. Builder formally handed it off with unchanged frozen stage 1. Independent review initially received `b85125091c8fd86408725b090fcc7cab77cd7129` and then received the complete cumulative requirements again with the updated target; any earlier revision evidence must retain its original identity.

Builder's final isolated run `stage2-official-02` passed 120/120 stage-1 and 25/25 stage-2 cases, zero required failures/errors/skips/deselections, in 40.588579 seconds total (17.41s and 14.46s suite times). The expected stage-3 probe collected 7 but stopped after one missing-policy-endpoint failure; 6 were not run. The probe is not a required-stage failure. These 145 shipped cases are partial coverage.

Builder's final focused API run `stage2-api-02` passed 11 scenario families across 199 requests in 2.352373 seconds. Its final headless Chrome run `stage2-browser-03` passed 21 scenario families, had zero JavaScript page errors and produced 23 screenshots in 24.076315 seconds. Browser evidence includes 375/1440 layouts, long labels, actual Tab navigation, stale/delayed/failed responses, uncertain single/pair retries and migration. These are Builder checks, separate from independent acceptance, and repetitions are not new distinct cases.

The first browser round's two failures were traced to a programmatic-focus test precondition; that original failed run remains preserved and is not represented as two product defects. A real control-boundary contrast measurement of 2.736:1 led to a source improvement; final recorded field and available-seat boundaries are 3.696:1 and 3.456:1, with text at least 4.5:1. Coordinator visually inspected selected actual screenshots at the immediately preceding presentation revision `5d838a713954e8dd0c53e1e0a84847aa77b68faf`; that limited observation does not substitute for interactions or final exact-commit review.

The full implementation handoff is `agent-evidence/builder/stage-2-handoff.md`; official, API and browser directories each have original command/timing/exit logs. No independent stage-2 decision has yet been recorded in this ledger.

The Builder must copy accepted stage 1 forward and extend only `stage-2/`. The frozen source tree is `dfff49710165dc7d568496f1d230b4fc69eb7b2c`, accepted at `ec96785a3aaa611e8519d09869cade8ffddb9224`. The subsequent Planner commit `df40fb0` contains documentation only. The complete cumulative specifications and prepared environment were pasted into stage-2 handoff `1cb101f9-24c9-496a-b588-5822e77bd986`.

## Review independence and chronology

Reviewer derived the stage-2 map from the complete stage-1 and stage-2 text, while the result had no stage-2 folder at its initial check (`2026-09-27T05:59:34.832777Z`). The map was completed at `06:10:42.300Z`, before the stage-2 copy at approximately `06:12:42.5Z`. The final preparation seal was `06:14:30.646260Z`, and explicitly records no stage-2 source inspection. The coordinator clarified that the operator's actual requirement is scenarios derived before implementation inspection; the final administrative seal is not falsely described as preceding all code creation. The map adds 88 planned families to the 110 inherited stage-1 families; these counts are not executions.

The map distinguishes required product assertions, the assigned generic context/accessibility quality checks and exploratory observations. It inherits stage-1 invariants without retroactively changing historical receipt shapes. It does not add stage-3 policies/history/recurrence or stage-4 closure behavior to this folder.

## Acceptance journeys

Required evidence includes cumulative API conformance; approved-pair order, capacity and every-member occupancy; atomic swaps and rollback; direct HTML routes; signed-out browsing and signed-in identity; successful and repeated booking; combined confirmation/lookup/cancellation; rejected stale availability with retained input; delayed competing searches; lost committed-response recovery with the same body/key; and stage-1 import preserving sessions and original receipts.

Independent real-browser checks use the installed Chrome channel headlessly through Playwright in isolated synthetic contexts. Screenshots and DOM/viewport evidence cover 375 and 1440 CSS pixels, long labels, visible form labels, keyboard focus and operation, readable feedback, and no horizontal page overflow. Delayed success/error/cleanup from a superseded search, selection, route or user must not replace current intent. Visible identities and results must be compared with authoritative API state.

Stage-1 is API-only. Any browser upgrade harness must describe the actual compatible legacy client arrangement; it cannot claim a stage-1 browser product existed. Pending retry identity/body must not be rewritten by a test to fake migration compatibility. Coverage limitations remain explicit.

## Completion gate

Accept only an exact committed stage-2 tree after official isolated cumulative checks, independent API/browser checks, preserved failure/repair evidence and an explicit Reviewer decision. Record the expected stage-3 probe separately. No stage-3 folder may be copied forward before that acceptance. Actual counts and timings will be added from completed reports, never predicted.
