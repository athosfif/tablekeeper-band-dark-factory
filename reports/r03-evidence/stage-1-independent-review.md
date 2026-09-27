# Stage 1 repair recheck — ACCEPT

**ACCEPT ec96785a3aaa611e8519d09869cade8ffddb9224**, stage tree **dfff49710165dc7d568496f1d230b4fc69eb7b2c**, repository tree `8a91b3383e513bb240b5cab046d52af76e3ab390`.

Independent HTTP rechecks confirm all four originally failing cases now pass, the official isolated stage-1 suite passes, and no remaining defect was observed in this revision's exercised scope. The rejection and original evidence for `d542ba1ac20d8bd4d62a7a938450d4526f64bed0` remain unchanged. Acceptance is tied to this exact snapshot; it is not acceptance of any subsequent source change or future stage.

## Original failures rechecked without weakening expectations

| Original reproduction | Old result | Repaired result |
|---|---|---|
| Accepted create with unknown JSON `ignored:1e309`, then export | Export 422 | Create 201, export 200 |
| Same key with ignored value changed from 1e309 to 1e310 | Replay 200 | 409 idempotency_key_reuse |
| Decimal integer 10**400 party against capacity 4 | 422 validation_failed | 422 party_exceeds_capacity |
| Fixture capacity 10**400 and equal valid integer party | Booking 422 | Reset 204, booking 201 |

The same `independent.py` and `supplemental.py` reproduction files were copied byte-for-byte from the earlier review in this fresh room. No earlier submission material was used. The four original failed cases appear under their original case IDs in `supplemental-01.stdout`; all eight cases in that supplemental script now pass.

## Counts and timings

| Run | Outcome | Command elapsed |
|---|---|---:|
| `official-01` | 120/120 required tests pass; suite 18.34s | 71.843s including builds and probe |
| Stage-2 overshoot probe within official-01 | 25 collected, 1 executed/failed on absent UI, 24 not run; 16.32s | Included above |
| `independent-01` | 63/63 pass | 8.029s |
| `supplemental-01` | 8/8 pass, including four original failures | 1.868s |
| `numeric-01` | 15/15 new focused cases pass | 3.186s |
| Standalone image `build` | Pass | 4.170s |

This revision: **86 distinct independent cases / 86 cumulative independent case executions, all passed**, with 715 recorded HTTP exchanges plus the committed-response relay interaction. The maximum recorded independent request was approximately 0.170 seconds; no 5xx or timeout occurred. Race request counts and snapshot-loop iterations are not inflated into extra cases.

Across the two reviewer revisions: **86 distinct independent case IDs / 157 cumulative case executions** (71 old + 86 repair); 4 failures remain in the original evidence and are now rechecked successfully. Official stage 1: **120 distinct official tests / 240 cumulative executions**, all passed. Expected probes are separate: one executed failure per revision, not 25 executed failures. Official and independent semantic coverage overlaps and is not summed as unique requirements.

## New numeric and portability evidence

`numeric.py` adds six same-value representations (including `1`/`1.0`, large exponent equivalents, tiny exponents, integer/decimal precision and negative zero), six distinct-value checks (close decimals, tiny nonzero values, adjacent large values, boolean versus number, array order and nested huge values), one exact-number create-receipt export/import/rollback case, one batch-receipt portability case after cancellation, and one integer-valued decimal party case. All 15 pass.

The portability cases preserve the export's raw bytes when importing, parse exported numbers independently with Decimal, and redact tokens/state from output. They confirm old tokens, original immutable receipts and current amended/cancelled records across two independent containers/ports, changed-body conflicts after import, invalid-import rollback and repeat replacement. This avoids a test-client float conversion accidentally changing the snapshot before import.

Re-run independent coverage also includes auth/privacy, body/query types, cutoff precedence, first-fold/gap/absolute DST rules, immutable receipt identity after mutation, same-key/different-key 50-request races, batch swaps/rollback, 20 concurrent snapshot iterations, and an actual local relay dropping an upstream committed response followed by same-body/key recovery. There is no stage-1 UI requirement.

## Revision and runtime integrity

The result was cloned into this reviewer evidence folder and detached at the full handoff commit. Builder's working tree/index and Planner-owned root documentation were untouched. The official package remains at `803560d2a678ace1414465c098eb0ab5380ffade` with unchanged tracked files. `verification.json` checks the exact revision/tree, clean clone, every tracked build-context byte against its Git blob, runtime limits and artifact hashes.

The previously verified tar transport tool was reused from reviewer evidence to avoid the already reproduced macOS AppleDouble xattr transfer failure. The official CLI, tests and Dockerfile bytes were not patched; there was no global configuration change. Source/harness build contexts and original/transport argv are recorded in `build-context-*.json`. All commands have full argv, UTC start/end, elapsed/exit status and stdout/stderr in matching evidence files.

The committed Dockerfile was rebuilt. Independent services ran in an internal Docker network with 2 vCPU, 2 GiB, no product source/data mounts, one service process, default 8080 and alternate PORT=9090. Both served the checks. All task-owned service containers and network were removed after evidence capture. Images and evidence remain for reproducibility.

Post-test source audit corroborates exact Decimal parsing/serialization for ignored fields and receipts, numeric equality that keeps booleans distinct, and integer validation without float conversion. The hash, lock, response-copy and snapshot invariants checked in the first review are retained. The patch also decodes opaque route identifiers after path segmentation and fixes source-file read permissions in the image. Acceptance comes from independent behavior and official reruns, not this audit or Builder's report alone.

## Limits and next gate

No known exercised failure remains. Shipped tests are partial, and the 86 independent cases do not claim every variant in the 110-family map or exhaustive scheduler exploration. Source-stop-after-export and every pathological input variant were not separately executed; ordinary no-shared-volume cross-container portability was verified. No restart persistence or browser UI is required here. The host-volume direct-build xattr issue remains environmental; the byte-verified tar route works. The official runner's read-only pytest-cache warnings do not change passed counts or authorize making official files writable.

This acceptance permits freezing the exact stage-1 tree. The separately assigned stage-2 pre-implementation map must still be completed/sealed before stage-2 source is created; its draft was preserved when this priority recheck arrived. Shared task #2 remains in progress for the subsequent stages.
