# Stage 2 exact-revision review — ACCEPT

**ACCEPT `e44838741cc906fbcae88e4248b5dc850af90e7c` for the stage-2 gate.** All three original raw-wire numeric defects are resolved on this exact image. The full required official gate and the independently rerun API/browser checks pass. No unresolved observed defect blocks this revision. Earlier rejections remain valid for their original commits and are preserved unchanged.

| Identity | Verified value |
|---|---|
| Commit | `e44838741cc906fbcae88e4248b5dc850af90e7c` |
| Repository tree | `b7d2e49140f4df8ad7b6c6a6ce9a05c711e2bf10` |
| Stage-2 tree | `b33e79f9bb65ff730b626f9c774afa4653b11e59` |
| Frozen stage-1 tree | `dfff49710165dc7d568496f1d230b4fc69eb7b2c` — unchanged |
| Official input HEAD | `803560d2a678ace1414465c098eb0ab5380ffade` — tracked bytes unchanged |
| Independently built image | `sha256:f14448a31719d4d38f8ee32c1986aeb6fb0621790c02172bbe5090d2889c5fcd` |

Evidence directory: `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence/reviewer/review-e448387`. Tests used its detached `checkout/`, never the live repository's uncommitted documentation. `snapshot-verification.json`, `transport-verification.json`, `diff.stdout` and the final manifest make this review inspectable.

## Chronology and changed risk

The existing sealed stage-2 map and approach were inherited. The 20-family numeric supplement `numeric-boundary-map.md` was fixed at **2026-09-27 07:32:25.420595 UTC**, before new source inspection at **07:32:34.196712 UTC**. `boundary-seal.json` records their hashes and zero product tests at that point. Expectations come from the supplied specifications and independent synthetic fixtures, not Builder tests.

The complete product diff from 050edd1 changes five paths: RUN.md documents exact numbers; server.py adds only the local codec's static route; index.html loads that codec before app.js; the new exact-json.js parses/serializes numeric tokens without binary-float rounding; app.js uses it for API/session JSON, exact positive-integer input and pair-capacity arithmetic, and displays the party count in confirmations. CSS and the API domain/state/security logic are unchanged. Every frozen stage-1 byte is unchanged. The broad browser rerun below was necessary because parsing and serialization affect authentication, errors, searches, booking, retries and lookup—not just one input.

## Original failures and numeric boundaries

`large-party-repro.js` is byte-identical to the original independent 9703131 reproduction. Its three cases now pass in **4.441842 s**:

| Original case | Actual result on e448387 |
|---|---|
| Single creation with visible `9007199254740993` | Raw POST contains unquoted numeric `9007199254740993`; authoritative stored list retains it exactly |
| Pair creation with the same count | Raw POST and stored booking retain the exact number and declared pair |
| Lookup of an exact API-created booking | Raw receipt and actual visible Guests text both contain `9007199254740993` |

Use the `raw_post_body`, `raw_authoritative_list`, `raw_receipt` and `visible_detail` evidence in `large-party-repro-01.json`. The unchanged script also has a legacy diagnostic `requests.body` parsed with native JavaScript JSON; that diagnostic rounds unsafe integers and is **not the assertion oracle**. It is retained without alteration. The raw assertions establish the pass. The added numeric suite captures raw requests throughout.

`numeric-browser.js` adds **24 passing browser/API journeys** in **43.475372 s**. Single and pair modes preserve neighboring values 9007199254740992/993/994; unchanged submissions retain key/body/reference, including after cancellation, while a mathematically changed count creates a new key and new booking. Ordinary 1/2/4/6 and integral spellings 4.0/4e0 work as numbers. Fractional, nonpositive and a long fractional spelling are refused without a booking or false confirmation; raw API string/boolean/fractional values receive the specified validation error. Pair capacity `9007199254740993 + 1` displays and admits exactly 9007199254740994. Both seating modes also preserve a 40-digit integer through actual creation, storage and lookup. Numeric-looking/prototype-like opaque IDs remain strings, and quotes, backslashes and Unicode labels retain their identity.

Actual lost-committed-response recovery was exercised with the same DOM input, retained signed-in identity, original raw body and key through import. One journey uses the real accepted stage-1 API as source, exports its unchanged old receipt, imports into stage 2 and switches the fixed local API relay between requests. Stage 1 has no invented UI: the compatible stage-2 shell is held while using that actual stage-1 service. Two other journeys migrate a live stage-2 pending single/pair form from one container to another. Replays return the original reference and response, remove uncertainty/error, and produce exactly one stored booking. Synthetic export files are private evidence, not public artifacts.

## Required official gate and independently executed coverage

| Suite on this exact image | Cases/executions | Result | Actual time |
|---|---:|---|---:|
| Official cumulative stage 1 | 120 | 120 passed | pytest 21.09 s |
| Official stage 2 | 25 | 25 passed | pytest 33.53 s |
| Full official isolated command | 145 required | pass | 129.845875 s |
| Separate expected stage-3 probe | 7 collected, 1 executed | missing policies endpoint: expected 404 instead of stage-3 201; 6 unexecuted | pytest 0.30 s |
| Independent API core | 63 | 63 passed | 13.757152 s |
| API supplemental | 8 | 8 passed | 4.045234 s |
| API exact-number regression | 15 | 15 passed | 4.512484 s |
| API combinations/moves/imports | 25 | 25 passed | 6.640370 s |
| Main browser | 26 | 26 passed | 52.803369 s |
| Extra async/migration browser | 10 | 10 passed | 16.517289 s |
| Browser keyboard/boundary | 2 | 2 passed | 6.413977 s |
| Caption/keyboard viewports | 2 | 2 passed | 13.601914 s |
| Original raw numeric reproductions | 3 | 3 passed | 4.441842 s |
| Added numeric journeys | 24 | 24 passed | 43.475372 s |

Independent totals are **176 distinct named cases, 178 executions, all passing**: 111 API cases and 65 browser/hybrid cases. The browser files execute 67 cases because the pair-refusal case and original large-single case each occur twice. The added numeric journeys combine several assertions; counts do not claim 176 disjoint requirements. The API suites record **1,007 HTTP events**; browser files include 328 mixed HTTP/visual/identity evidence events, not 328 additional cases. The official 145 are separate. Prior revision reruns are not counted as new distinct cases, and preparation-oracle self-checks contribute zero product cases.

The independent API rerun covers cumulative validation, error precedence, DST, cutoffs, half-open occupancy, races, idempotency, failed-key reuse, original receipts, export/import and atomic replacement, pair order/capacity/non-transitivity, every-member conflicts, concurrent creates/amendments/moves and actual stage-1 migration. Browser coverage reruns all required routes and auth identity/logout, both seating flows/repeats/lookup/cancellation, authoritative grid flags, stale searches including delayed restaurant labels, competing-booking rejection with retained input and refreshed availability, committed response loss, delayed success/error/cleanup after selection/party/route/session changes, duplicate Enter, and lookup/cancel identity changes. Assertions compare visible identity/state with actual stored bookings.

The only checker change was made **before execution**: the duplicate large-number case in browser-boundaries.js now asserts the raw POST rather than parsing that number through native JavaScript JSON. Its original script and `pre-execution-checker-note.json` remain. No assertion of the three original raw reproductions was changed. There are no product-test or setup failures in these executed suites. A later evidence-file inventory accidentally encountered an AppleDouble metadata file and raised a UnicodeDecodeError; the read-only inventory was repeated excluding `._` files. This was not a product check or a changed test result. Read-only official pytest-cache warnings are retained.

## Actual presentation and deployment evidence

Installed headless Chrome ran isolated synthetic contexts at **375×812 and 1440×1000**, including long names, explicit labels, actual Tab/Enter selection/submission, visible focus, and available/unavailable/selected/loading/refused/uncertain/success states. Both viewport caption journeys passed. There are **94 repeated shared-gold text observations**, with lowest measured contrast **5.315248802966871:1**, not 94 cases or a full WCAG certification. Page overflow checks passed. The 40-digit lookup wraps inside the mobile panel. Reviewer visually inspected mobile confirmation, desktop focused pair, mobile 40-digit pair lookup and mobile uncertainty screenshots; hierarchy and wrapping remain coherent. All **63 screenshots** are retained, and browser cases observed no page errors.

The served app.js, exact-json.js, app.css and index.html exactly matched their committed bytes. The codec SHA-256 is `d6f84bf157cb53bd643a8d1bf4b8df70c5733835f4dce6755da70876588b02a5`; stylesheet SHA-256 remains `a887ba0262546f6de3687fa6c8dc7fdaa5515fc0ef78d49b40c0730e60f3b34e`. Browser external-origin requests were blocked. The local assets functioned without outside dependencies.

Every executed command has full argv, cwd, UTC start/end, duration and exit in a `.command.json`, plus complete stdout/stderr. `official-01.command.json` records the exact `python -m harness run --track tablekeeper --repo <detached checkout> --stage 2 --mode isolated --out <fresh official-01>` invocation; no test filters were supplied. API commands use the cached Python image with reviewer files read-only; browser commands use the supplied Node/Playwright/Chrome paths. `record.py` reproduces the recording mechanism.

The evidence-only Docker tar transport was verified against Git for all four build contexts: stage 2 twice (17 files each), official harness (14) and frozen stage 1 (11). No product or official bytes were modified. Direct image build took **5.255755 s**. Candidate containers tested default port 8080 and explicit PORT=9090, each with 2 CPU/2 GiB, no product volumes, and only an internal network. The accepted stage-1 source image remained `sha256:65848d04ff0c54ee082217375a115261fd7a079d895d129378fff5ab2db26b95`. A fixed-destination local relay provided ingress, without granting outbound access to the product containers. Runtime inspections and all four container logs were retained; only this review's four containers and internal network were removed afterwards.

## Carried and unexecuted boundaries

All prior independent API/browser cases described above were actually rerun on e448387; their pass counts are not inherited from Builder or prior images. The source-blind acceptance maps and earlier failure chronology are inherited evidence, not new passes. Reports under review-b851250, review-9703131 and review-050edd1 remain attributed to their original hashes. The 9703131 and 050edd1 numeric failures are resolved here without erasing them.

This is finite independent stage-2 acceptance, not proof of all hidden checks, every possible JSON token length or every asynchronous schedule. No arbitrary resource-exhaustion input, every browser engine, full accessibility certification, stage-3/4 product acceptance or final all-folder gate is claimed. The stage-3 probe was expected to fail and is not a stage-2 defect. Stage-3 and stage-4 preparation remains sealed/source-blind; no product folder for either was inspected or created. No tool blocker remains. Coordinator owns the freeze and later source authorization. Shared task #2 remains in_progress.
