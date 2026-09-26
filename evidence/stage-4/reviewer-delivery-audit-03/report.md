# Final four-stage delivery audit

**ACCEPT delivery revision `40bb319c25fed8ee3c57b3364e997e71b1c87e6c` for the authorized final packaging scope. All four service folders remain independently ready locally.**

The repository is `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/submission-tablekeeper`. The revision was clean before and after this audit. Its sole parent is the independently accepted source `8c6df7f369f0041798abf8de0e10c0babf501df5`; its only changes are root `README.md`, `FACTORY.md`, `plan.md` and new `STAGE-4-REPORT.md`. No documentation claim requiring repair was found. The output repository, mandates, official inputs and earlier evidence were not modified.

This accepts the assigned local delivery, not official submission gates. The unchanged official offline check on a fresh Linux materialization reports exactly one problem: **`room.json is missing`**. Actual exported seat identities and reciprocal room exchanges therefore remain unverified by that submission check. The real full-room export and its privacy review remain operator work.

## Accepted trees and preserved history

| Folder | Independently accepted source | Delivery tree |
|---|---|---|
| stage-1 | `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8` | `0050accbdc6d0457ffdc73de6365158e65c1808b` |
| stage-2 | `2e026c006569b2e749de79b7526f03ae9b6e44e3` | `2ebbd48a3ba2b6de7eba2a5fcd851a36efc4e2c8` |
| stage-3 | `4b7b0620f3dd645fac18d840a6d612e8f4c6bed6` | `6f4bee6bec0d5908de7ebe9345290f786b012b63` |
| stage-4 | `8c6df7f369f0041798abf8de0e10c0babf501df5` | `e4bae830ae426197911968153c97c4ef06f9e40d` |

All four delivery trees equal their individually accepted trees and the trees exercised together in `../reviewer-package-01`. The mandates tree remains `fbfd2dd5db832c375091a0b3a63bb944cd3ec859` and is unchanged from initial baseline `9e02c181e3bcefdf3abbe272ba777eed614b8256`. Each of the three generic mandate files names Codex and `gpt-6-astra`; none contains track-specific requirements. The 17-commit history, accepted sources, rejected Stage 2/4 sources and original preparation baseline remain reachable. Historical Stage 1/2/3 reports are unchanged. See `history.txt`, `committed-inventory.json` and `audit.json`.

The active room plan was read through `jam plan show` and reconfirmed at the end of inspection. Its immutable snapshot is labeled **Four stages independently ready — final delivery acceptance map**, contains **16,580 bytes**, and is byte-identical to committed `plan.md`. SHA256: `422f34ea4a74ee020305106ad87fb9f3a9bdd30010949ccc819ea7be3e105e43`. The existing active snapshot was not replaced.

## Fresh materialization and package inspection

The audit materialized all **66 regular committed files**, preserving blob contents and executable modes. No tracked symlink, gitlink/submodule, nested Git entry or `.gitmodules` exists. Stage folders contain respectively **8, 13, 15 and 19 files**. Each has its own Dockerfile, RUN.md and complete local Python modules. Runtime imports resolve within that folder or Python's standard library; each Docker COPY input exists inside its own context. Stages 2–4 contain HTML, JavaScript and CSS. Their Dockerfiles install Liberation fonts and its license into the image during build; no remote font/script/style fetch is referenced at runtime. Build-time package acquisition is permitted. The previously executed isolated builds and UI flows establish runtime behavior for these identical trees.

Fresh Linux materialization avoids host AppleDouble metadata. A USTAR stream contains exact committed submission blobs and unchanged pinned official harness/Tablekeeper files. It runs the **unchanged** command `python -B -m harness check /audit/submission --track tablekeeper` from `/audit/official`, inside cached image `sha256:5affa5a904096b12fd9b881fdc597202a348ccfb9f39ee5202c8b52958ec15c4`, with `--network=none --cpus=2 --memory=2g`, no mounts and no image pull. This is a packaging check, not a new service conformance run.

Observed check: **exit 1, 0.400981 seconds, one problem: missing `room.json`**. Layout, present mandates and credential scanning produced no additional findings. `harness-check-linux.log` preserves the actual output. The transport manifest is `linux-transport-provenance.json`; archive SHA256 is `e8aaa5513ca0eda96c46366a5296a4f6a7d686c8346855f98337bf3ce0b7ebbe`. Source checkout remains pinned at `803560d2a678ace1414465c098eb0ab5380ffade` with no tracked change. Complete guide/spec line counts match the plan: 877 and 472/240/240/109.

The authorized-package history scan examined **95 distinct reachable committed blob/path versions**, using unchanged official credential patterns plus private-key headers, and found **zero matches**. The current inventory includes no saved state exports, session databases, environment-secret files or room export. Synthetic fixtures and source code remain distinguishable from runtime secrets. Pattern scanning is heuristic; it does not certify the future room export or every conceivable private value.

## Evidence attribution and documentation claims

README.md, FACTORY.md, plan.md and all four stage reports were read. Material counts, source revisions, repair descriptions, runtime boundaries and remaining operator work agree with retained evidence. Historical reports describe historical checkpoints; the final report supplies the completed package result. In particular:

| Claim | Checked evidence |
|---|---|
| Stage 1 independent totals | Its final source/delivery audits distinguish the 27-group/955-call full run from the additional 1-group/13-call supplement: 28 distinct groups and 968 calls, as FACTORY.md says. |
| Stage 2 | Exact accepted source metadata and logs: 36 API groups in 14.461s, 1,205 instrumented calls; 10 browser groups in 21.669s. Long-label mobile rejection and wrapping repair remain preserved. |
| Stage 3 | Exact accepted source metadata and logs: 55 API groups in 19.284s, 1,789 calls; 11 browser groups in 21.839s plus one unique policy case in 1.381s. Strengthened observation is not claimed as a source repair or two distinct cases. |
| Stage 4 independent | `reviewer-api-repair-02`: 75/75 groups, 2,585 calls, zero failures/errors/5xx, 31.379s tests/32.223s command. `reviewer-browser-repair-03`: 17/17, 36.542s tests/37.828s command, 91 direct setup/control calls plus browser traffic. Both actually ran at accepted `8c6df7f...`. |
| Stage 4 repair | Parent `d6b3c0f...` preserved correct immutable receipts but stale confirmation seating. Independent single/pair reproduction rejected it. Current-detail refresh repair passed independent tests and Planner's original regression. |
| Supplemental evidence | Planner optimizer 9/9 ran on rejected parent with unchanged API/solver; Planner UI regression ran on exact accepted source. Builder's 9-group focused repair ran precommit on app/test bytes whose hashes match the committed files. These are not reclassified as independent Reviewer runs. |
| Resource and cost statements | Final independent API maxima 3.489738668s ordinary/0.195503209s controls; health at most 0.698913s. Internal/no-egress constrained runs are distinguished from ordinary RUN.md smoke and Planner/Builder runs. Wall-clock checkpoints are not billed model time. Model spend remains unavailable. |

### Completed official isolated package, reused by exact tree equality

`../reviewer-package-01` actually ran **`--all --mode isolated` at `8c6df7f369f0041798abf8de0e10c0babf501df5`**, exit 0, **202.442385s command / 203.385147s whole run**. This audit compared its before/after revision and clean-status records, tree records, every per-folder report and every count file. No application test rerun is claimed at the later prose-only delivery commit.

| Folder | Complete cumulative passing suites | Total | Claimed stage |
|---|---|---:|---:|
| stage-1 | 120/120, 20.69s | 120 | 1 |
| stage-2 | 120/120, 16.95s; 25/25, 16.62s | 145 | 2 |
| stage-3 | 120/120, 21.75s; 25/25, 21.19s; 7/7, 1.06s | 152 | 3 |
| stage-4 | 120/120, 21.91s; 25/25, 27.54s; 7/7, 1.28s; 6/6, 1.14s | 158 | 4 |

**575/575 cumulative conformance executions**, with zero failures/errors/skips/deselections/xfails/unexecuted cases within those suites. These are executions across folders, not 575 distinct tests.

Expected later-stage probes remain separate and genuinely fail: Stage 1→2 **0 passed/1 failed/24 unexecuted** of 25 (11.51s, absent browser route); Stage 2→3 **0/1/6** of 7 (0.22s, absent policy endpoint); Stage 3→4 **4/1/1** of 6 (0.82s, absent series amendment endpoint). The original official fail-fast leaves those cases unexecuted; no unexecuted probe is counted as a pass. Stage 4 has no next-stage probe. Probe logs were inspected, not inferred only from the summary's null overshoot field.

The existing official Docker context adapter's SHA256 is verified as `db517e1e10039f5725044151cfbf6e13dc1ee3b944f31ec3f735800bd9ab7d02`. It filters AppleDouble/cache transport entries while preserving ordinary official bytes. The final audit's separate Linux materialization also preserves official bytes; neither changes supplied tests, test flags or source.

## Preserved audit tooling issues

`../reviewer-delivery-audit-01` retains the first incomplete audit: host-created AppleDouble was mistakenly traversed as Python (UnicodeDecodeError). Its diagnostic host `harness check` reported six metadata-only mandate findings plus missing room.json. `../reviewer-delivery-audit-02` successfully performed the Linux check and history scan, then stopped on a reviewer assertion expecting zero bytes in old clean-status logs; the prior runner represents empty output with one newline. Version 03 corrects that log-format assumption. Neither failure is a product/documentation defect; neither is relabeled a complete pass. Their scripts, partial results and notes remain. A subsequent read-only digest helper also used an unresolved relative evidence path and was immediately corrected to the assigned absolute path; it changed no input or verdict.

The final audit script completed in **8.421090 seconds**; this duration excludes manual document/evidence review. Reproduction from the assigned evidence workspace is the prepared Python `-B` invocation of this directory's `audit.py`; it refuses to overwrite evidence, so copy the public audit script into a new unique directory first. `audit.json` records exact argv/cwd/exit/timing, checks and provenance.

## Final boundaries

All four standalone service folders are independently ready on the written requirements and observed evidence. No known reproduced service or final documentation defect remains. Finite tests are not a guarantee about hidden judging or every possible schedule. The full-room export, privacy review, final presentation/video, public publication, clean-clone submission checks and event submission remain operator tasks. No export, publication, submission or official acceptance is claimed. Accepted service source and mandates remain frozen; the authorized review concludes with this delivery verdict.
