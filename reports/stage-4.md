# Stage 4 acceptance ledger

Status: independent preparation complete; implementation and acceptance pending prior stages. No stage-4 product checks have run.

Reviewer derived 93 additional scenario families (87 requirements, 2 generic-mandate checks, 4 observations), for 394 cumulative prepared families. These are not product executions. Preparation was sealed at `2026-09-27T07:08:33.968823Z`; no stage-3 or stage-4 source folder was present or inspected.

The independent planning oracle compares exhaustive Cartesian search with a separately structured backtracking search. Its selfcheck used 18 hand-derived and 80 deterministically generated fixtures plus 3 bound checks, in 7.274711791 seconds. The maximum supported-dimension fixture examined 262144 candidates. These results validate the review oracle only: zero product requests or product passes are claimed.

Evidence is under `agent-evidence/reviewer/stage-4-acceptance-map.md`, `stage-4-checking-approach.md`, `stage-4-planning-oracle.py` and `stage-4-preparation-manifest.json`. The map's SHA256 is `6ef169f2361b6e2d9436bad9b709bd2598444f127f88e70701ee12afef93dee1`.

The gate covers the full lexicographic objective, each booking's accepted capacities, fixed bookings and entire-interval conflicts, read-only previews, restaurant revisions and stale/apply/replay races, atomic closures, histories and series flags, recurring amendments and error precedence, imports from every earlier folder, and authoritative current seating in existing browser screens. An accepted exact revision still requires final all-folder isolated verification of the complete package.
