# Tablekeeper — Figueira factory run r03

Fresh, local Tablekeeper implementation produced by three configured agent seats in Band room `769c0fe4-0d50-4507-9c8a-1ed742e1c477`, following one human dispatch for the four-stage sequence. The authoritative read-only challenge checkout was verified at `803560d2a678ace1414465c098eb0ab5380ffade`.

## Current delivery state

Work is in progress. Stage 1 is independently accepted at `ec96785a3aaa611e8519d09869cade8ffddb9224`, with frozen tree `dfff49710165dc7d568496f1d230b4fc69eb7b2c`: 120/120 shipped tests and 86/86 independent cases passed. Stage 2 is independently accepted at `e44838741cc906fbcae88e4248b5dc850af90e7c`, frozen tree `b33e79f9bb65ff730b626f9c774afa4653b11e59`: 145/145 shipped tests and 176 distinct independent cases in 178 passing executions. Stage3 is implemented at `6b75841c243ea4722be08834526545ea847bad27` and under independent review; stage4 awaits that acceptance. Original rejections and verified repairs remain preserved. These finite checks do not establish hidden-test correctness. Later folders are added only by copying the preceding independently accepted folder and extending that copy.

- [plan.md](plan.md) records the sequence and acceptance map.
- [FACTORY.md](FACTORY.md) records seat responsibilities, reproducibility, decisions, costs and failure handling.
- [reports/acceptance.json](reports/acceptance.json) records exact acceptance identities and per-revision counts.
- `mandates/` contains exact copies of the three supplied generic mandates.
- `stage-N/RUN.md`, when present, describes that folder's standalone build and runtime.

Evidence is preserved at `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence`. This is the authorized run evidence location, not a runtime dependency. The source repository and each completed stage must build independently of it.

## Scope and provenance

No previous submission source, historical room or product-specific bug report was input to this run. Official specifications and tests are not modified. Every agent commit is retained without amending, rebasing or squashing. Shipped official checks are partial conformance evidence, not proof of hidden-check correctness; next-stage probe failures are recorded separately from required suites.

`room.json` is intentionally absent until the operator supplies an authentic whole-room export after completion. It will not be fabricated. Publication, video, media, public verification and platform submission belong to the operator after the local factory outcome. This repository has not been published or submitted by the factory.
