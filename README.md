# Tablekeeper — Figueira factory run r03

Fresh, local Tablekeeper implementation produced by three configured agent seats in Band room `769c0fe4-0d50-4507-9c8a-1ed742e1c477`, following one human dispatch for the four-stage sequence. The authoritative read-only challenge checkout was verified at `803560d2a678ace1414465c098eb0ab5380ffade`.

## Current delivery state

Work is in progress. Stage 1 is independently accepted at `ec96785a3aaa611e8519d09869cade8ffddb9224`, with frozen stage tree `dfff49710165dc7d568496f1d230b4fc69eb7b2c`: 120/120 shipped official tests and 86/86 independent cases passed in the repair review. This does not establish hidden-test correctness. Stages 2–4 remain to be implemented and accepted. Later stage folders are added only by copying the preceding independently accepted folder and extending that copy.

- [plan.md](plan.md) records the sequence and acceptance map.
- [FACTORY.md](FACTORY.md) records seat responsibilities, reproducibility, decisions, costs and failure handling.
- `mandates/` contains exact copies of the three supplied generic mandates.
- `stage-N/RUN.md`, when present, describes that folder's standalone build and runtime.

Evidence is preserved at `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence`. This is the authorized run evidence location, not a runtime dependency. The source repository and each completed stage must build independently of it.

## Scope and provenance

No previous submission source, historical room or product-specific bug report was input to this run. Official specifications and tests are not modified. Every agent commit is retained without amending, rebasing or squashing. Shipped official checks are partial conformance evidence, not proof of hidden-check correctness; next-stage probe failures are recorded separately from required suites.

`room.json` is intentionally absent until the operator supplies an authentic whole-room export after completion. It will not be fabricated. Publication, video, media, public verification and platform submission belong to the operator after the local factory outcome. This repository has not been published or submitted by the factory.
