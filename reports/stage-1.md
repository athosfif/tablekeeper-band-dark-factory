# Stage 1 evidence ledger

Status: **ACCEPTED** by independent Reviewer at `ec96785a3aaa611e8519d09869cade8ffddb9224`, stage tree `dfff49710165dc7d568496f1d230b4fc69eb7b2c`. The entries below preserve the earlier candidates, failures and subsequent repair acceptance; they are not overwritten by the final pass.

Specification: the complete `tablekeeper/spec/stage-1.md` at official commit `803560d2a678ace1414465c098eb0ab5380ffade`; participant guide and clean-container contract apply. This stage is a JSON API only.

## Independent preparation

Reviewer sealed 110 scenario families before any implementation existed, at documentation-only result revision `db34ec338ccb376a028af9f9fdee220b100f3c59`. These are planned scenario families, not 110 executed tests. The full map and checking approach are under `agent-evidence/reviewer/` in the assigned evidence root.

## Preserved implementation revisions

| Full commit | Change |
|---|---|
| `0e6a0a920ec52678a1619539fd9070fff9311b7e` | Validation, elapsed-time/DST rules and password hashing |
| `d542ba1ac20d8bd4d62a7a938450d4526f64bed0` | Complete initial API candidate, atomic moves and portable receipts |
| `7a156e41359075612c3618579bf021cfebe643a2` | Source permissions inside image for unprivileged runtime |
| `ffda35c0b5aa010e6e0333b178dfb1d9a43ac4c5` | Encoded opaque IDs and large party counts |
| `ec96785a3aaa611e8519d09869cade8ffddb9224` | Exact JSON numeric values in retry identity and portable state |

The independent review first rejected commit `d542ba1ac20d8bd4d62a7a938450d4526f64bed0`, with four reproduced failures: a huge ignored JSON exponent poisoned export; two different huge exponents shared a retry receipt; a huge integer party produced the wrong capacity error; and a matching huge capacity/party could not be booked. The first review passed all 120 shipped checks but only 67 of 71 independent cases. Builder's subsequent large-integer and exact-number commits had already been produced when the rejection arrived; this run does not claim that the later message caused an earlier repair. The rejection still prevented accepting the initial revision.

Reviewer independently rechecked the repaired full revision in `reviewer/review-ec96785/`, preserving the original scripts byte-for-byte and adding numeric/portability neighbors. The signed report and `verification.json` explicitly ACCEPT the exact revision/tree above: 120/120 required official tests and 86/86 independent cases passed. The four original failures all passed unchanged reproductions. Official command elapsed 71.843s (18.34s suite); independent groups took 8.029s, 1.868s and 3.186s. The next-stage probe collected 25 cases but stopped after one expected absent-UI failure; the remaining 24 were not run.

Across the two Reviewer snapshots there were 86 distinct independent case IDs and 157 cumulative executions (71 + 86), including the four preserved earlier failures. The official suite comprised 120 distinct tests and 240 Reviewer executions across those two revisions. Independent and official semantic coverage overlaps and is not added together as unique requirement coverage. Separate Builder executions below are separate evidence.

Reviewer limits: not every variant in the 110-family map was executed, nor exhaustive scheduler exploration; a separate source-stop-after-export case was not executed. Cross-container/no-shared-volume portability, original receipts, concurrent snapshots, private access, exact numeric values, dropped committed responses and 50-request races were verified. No stage-1 UI was required. The host-volume xattr transport issue remains environmental; byte-verified tar transport succeeded without source/test/global-config changes.

## Builder focused executions observed

| Evidence folder | Scenario executions | Pass | Fail | HTTP requests | Maximum observed request duration |
|---|---:|---:|---:|---:|---:|
| `builder/focused-01` | 0 | 0 | 0 | 0 | Not a product execution |
| `builder/focused-02` | 0 | 0 | 0 | 0 | Not a product execution |
| `builder/focused-03` | 16 | 15 | 1 | 380 | 0.119682 s |
| `builder/focused-04` | 16 | 16 | 0 | 380 | 0.096232 s |
| `builder/focused-05` | 18 | 18 | 0 | 389 | 0.384055 s |

These are repeated executions of overlapping scenario sets, not 50 distinct tests. HTTP requests are also not test-case counts. Builder reports include 50-request races, atomic swaps, all four specified DST dates, original receipts and portable sessions. Independent acceptance is separate.

## Startup and packaging evidence

`builder/official-01` failed before tests: Docker BuildKit rejected extended attributes on `stage-1/._.dockerignore`. The report recorded stage 1 as `error`, no checks, no claimed stage. The original log is preserved. Later build attempts and remediation evidence must be reconciled before claiming any official pass.

Builder subsequently ran the unchanged official harness from a fresh local clone inside the assigned evidence root. Coordinator compared all 65 tracked files with the authoritative checkout: none missing, none different, and clone HEAD equals `803560d2a678ace1414465c098eb0ab5380ffade`. The authoritative checkout remains unchanged. Removing generated AppleDouble metadata from a clean input clone changes the suite digest because the harness includes matching `._*.py` files in its hash; no official tracked code or tests were edited.

`builder/official-04`, at commit `ec96785a3aaa611e8519d09869cade8ffddb9224`, completed the stage-1 isolated suite with 120 collected, 120 passed, zero failed/errors/skips/deselections/xfails. Command duration was 102.028154 seconds, including the separately logged stage-2 probe, which failed as expected. The console claims stage 1 on shipped checks. The report's `overshoot` field is null despite the separately printed/logged probe; retain both originals rather than rewriting the official report. This is Builder-run conformance evidence, not independent acceptance.

Coordinator package preflight `coordinator/offline-preflight-01` found six metadata-derived mandate errors plus the absent `room.json`. Removing only the three generated AppleDouble mandate files in the fresh result fixed those six errors without changing mandate bytes. `coordinator/offline-preflight-02` then reported exactly one problem: missing authentic `room.json`. This offline check builds nothing and is not stage-1 API acceptance.

Absolute evidence root: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence`. Command logs and execution JSON preserve timing, working directory and exit code. Session-bearing exported state is private test data, not public report content.
