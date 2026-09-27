# Stage 2 acceptance ledger

Status: functional repair committed at `e44838741cc906fbcae88e4248b5dc850af90e7c` and under independent review. Prior candidates were explicitly rejected. No stage-2 acceptance or stage-3 implementation is authorized yet.

## Committed candidate and Builder evidence

The complete candidate is `97031312f2ddd12b118388b369fcce576827ba43`, stage-2 tree `a0a23761dd71132ffe6c8b8cae29e2407d7e4517`. Builder formally handed it off with unchanged frozen stage 1. Independent review initially received `b85125091c8fd86408725b090fcc7cab77cd7129` and then received the complete cumulative requirements again with the updated target; any earlier revision evidence must retain its original identity.

Builder's final isolated run `stage2-official-02` passed 120/120 stage-1 and 25/25 stage-2 cases, zero required failures/errors/skips/deselections, in 40.588579 seconds total (17.41s and 14.46s suite times). The expected stage-3 probe collected 7 but stopped after one missing-policy-endpoint failure; 6 were not run. The probe is not a required-stage failure. These 145 shipped cases are partial coverage.

Builder's final focused API run `stage2-api-02` passed 11 scenario families across 199 requests in 2.352373 seconds. Its final headless Chrome run `stage2-browser-03` passed 21 scenario families, had zero JavaScript page errors and produced 23 screenshots in 24.076315 seconds. Browser evidence includes 375/1440 layouts, long labels, actual Tab navigation, stale/delayed/failed responses, uncertain single/pair retries and migration. These are Builder checks, separate from independent acceptance, and repetitions are not new distinct cases.

The first browser round's two failures were traced to a programmatic-focus test precondition; that original failed run remains preserved and is not represented as two product defects. A real control-boundary contrast measurement of 2.736:1 led to a source improvement; recorded field and available-seat boundaries are 3.696:1 and 3.456:1. The Builder's initial broad claim that all text reached 4.5:1 was incorrect: independent pair captions measured 4.4826:1. The distinct caption repair below corrects that observation; no formal accessibility certification is claimed. Coordinator visually inspected selected actual screenshots at the immediately preceding presentation revision `5d838a713954e8dd0c53e1e0a84847aa77b68faf`; that limited observation does not substitute for interactions or final exact-commit review.

The full implementation handoff is `agent-evidence/builder/stage-2-handoff.md`; official, API and browser directories each have original command/timing/exit logs. Subsequent independent decisions follow.

## Independent rejections and preserved evidence

The early `b85125091c8fd86408725b090fcc7cab77cd7129` review was superseded, not an acceptance gate. Its official 145 cases and independent API 111 cases passed; browser checks covered 35 distinct cases in 36 executions, with a corrected reviewer assertion retained. Evidence stays attributed to that revision under `agent-evidence/reviewer/review-b851250/`.

Reviewer explicitly **rejected `97031312f2ddd12b118388b369fcce576827ba43`**, despite official 120/120 inherited and 25/25 stage-2 passes. A specification-valid fixture gives one table capacity 10000000000000000 and a declared pair with another table of capacity 2. Entering party size 9007199254740993 in the real UI silently sends and stores 9007199254740992 for both single and pair reservations. Creating the exact integer through raw HTTP instead preserves it in the service, but UI lookup displays the rounded value. These are three concrete browser failures; they are not extra specification restrictions or merely large-number observations. The repair must preserve numeric identity through input, wire serialization, response parsing, rendering and retries, without imposing an unsupported safe-integer ceiling.

That revision passed 111/111 independent API cases (1007 HTTP events); browser coverage was 39 distinct cases in 41 executions, with 36 latest passes and 3 failures. The single write failure was reproduced twice, so there were four failed executions but three distinct failing cases. The official command took 88.959s (19.10s stage 1; 26.20s stage 2); the expected stage-3 probe collected 7, executed one missing-policy failure and left 6 unexecuted. Full report, raw wire captures, scripts, timings and screenshots are retained in `agent-evidence/reviewer/review-9703131/`.

Builder's subsequent color-only commit `050edd1b12d0653e0e35b037bd91e14e52adb2ea`, stage-2 tree `d18c2995d499bbf366136e2b7d9d76b47dd708b6`, changes the shared gold from #9a602d to #8c5528. Builder and Reviewer independently measured pair captions improving from 4.4826236764:1 to 5.3152488030:1 at 375/1440. The contrast observation was non-gating and was not the cause of the functional rejection.

Reviewer explicitly **rejected 050edd1** because all three numeric failures remained. Fresh official results were again 120/120 and 25/25; command 50.904519s (17.43s and 19.09s suites), plus the separate expected probe (7 collected, 1 failed, 6 unexecuted; 0.22s). New-image independent checks total 30 distinct cases in 55 executions: latest outcomes 27 pass and 3 product failures. Execution outcomes were 51 passes, 3 product failures and one resolved reviewer setup DNS failure, preserved before correcting only the retired fixture hostname. Focused API checks passed 25/25 in 4.212441s; two viewport/keyboard/pair journeys passed in 13.613259s; the three numeric reproductions failed in 5.264894s. The 94 repeated contrast observations are measurements, not 94 cases. The broad prior async/migration checks were not rerun and remain attributed to 9703131. Evidence is `agent-evidence/reviewer/review-050edd1/review-report.md` and `verification.json` (SHA256 `59e5364055ec035c212c93e6a94440de4d97d61a4f59422c9cc2c804590e0b41`).

Planner assigned the Builder a distinct functional repair with the complete cumulative specifications and exact three reproductions. All failures, checker errors, original revision reports and successful rechecks remain preserved. No human input or environment blocker prevents the repair.

## Exact-integer repair candidate

Builder handed off `e44838741cc906fbcae88e4248b5dc850af90e7c`, stage-2 tree `b33e79f9bb65ff730b626f9c774afa4653b11e59`, repository tree `b7d2e49140f4df8ad7b6c6a6ce9a05c711e2bf10`, with stage 1 unchanged. Browser JSON now retains integer tokens as BigInt and decimal tokens exactly, and emits unquoted numeric JSON values. Guest validation uses decimal spelling rather than floating-point conversion or native number-input step validation. Pair capacities and visible guest counts use the same exact representation. Five stage-2 files changed; no API storage semantics, mandates or earlier-stage source changed.

The progressive commit `2707a57985582069249d0e1438f4ee36c2782903` passed 12 codec checks but omitted the new static asset from the server allowlist. Real browser tests failed with `ExactJSON is not defined` (0/3 original repro cases and 0/11 new journeys). The next commit serves the codec and resolves that integration failure. Both source revisions and all failed logs/screenshots are retained.

Final Builder checks: original reproductions 3/3 in 8.027884s; added numeric browser journeys 11/11 in 21.664716s; existing browser regressions 21/21 in 37.719616s; focused API families 11/11 across 199 requests in 3.922048s; codec cases 12/12 in 0.262000s. Browser coverage in this repair totals 35 named distinct scenarios and 52 executions across before/intermediate/final runs, with 17 failed executions representing the three original precision defects and fourteen manifestations of the single intermediate delivery defect. This does not mean seventeen distinct defects. The final official run passed 120/120 plus 25/25 in 120.841074s (20.05s and 26.69s suites); next-stage probe 7 collected, 1 expected failure, 6 not run, 0.19s. These are Builder results, not independent acceptance.

The new browser checks include neighboring exact integers, 25-digit counts, fractional refusal, equivalent exponent input, safe HTML-shaped labels and real retained same-stage pair/earlier-stage singleton import recovery with original body/key/token. The adapted reproduction's secondary Playwright `postDataJSON()` metadata remains lossy; the actual assertions and raw wire evidence use unchanged raw JSON strings, documented honestly in the handoff. All six task-owned Builder containers were logged and removed.

Full report: `agent-evidence/builder/stage-2-numeric-repair.md`. Committed/served-byte manifests, original scripts, commands and times accompany it. Independent review of this exact repair was assigned with the complete preserved specifications; its first 10-minute reply window elapsed without a response, so no acceptance is inferred and the request was not resent. The review's fresh local evidence directory is `agent-evidence/reviewer/review-e448387/`.

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
