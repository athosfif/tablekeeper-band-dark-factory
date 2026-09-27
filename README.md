# Tablekeeper — Figueira factory run r03

Fresh, local Tablekeeper implementation produced by three configured agent seats in Band room `769c0fe4-0d50-4507-9c8a-1ed742e1c477`, following one human dispatch for the four-stage sequence. The authoritative read-only challenge checkout was verified at `803560d2a678ace1414465c098eb0ab5380ffade`.

## Delivery and acceptance

All four stages are independently accepted. The final product revision is `bb417f29a586fe0771fcc728ab308584f00d5b9a`. Each folder was copied from the preceding accepted tree before extension. Earlier folders stay unchanged and independently buildable. The complete package revision, including this documentation, is recorded by the separate final all-folder execution described below.

| Folder | Product scope | Independent gate | Required official cases at that review | Distinct independent cases with passing evidence |
|---|---|---|---:|---:|
| [stage-1](stage-1/RUN.md) | JSON API, auth, bookings, atomic moves and portable state; no UI | Accepted | 120 | 86 |
| [stage-2](stage-2/RUN.md) | Declared table pairs and English browser workflows | Accepted | 145 | 176 |
| [stage-3](stage-3/RUN.md) | Dated policies, accepted terms, history and recurring agreements | Accepted | 152 | 290 |
| [stage-4](stage-4/RUN.md) | Exact closure replanning and atomic recurring amendments | Accepted | 158 | 511 |

These are per-stage review counts, not a sum of distinct requirements. Later suites repeat earlier cases. Original failures, repairs, setup/checker corrections and successful rechecks remain preserved. Finite shipped and independent checks do not prove hidden-test correctness. Full accepted commit/tree identifiers, execution counts and timings are in the stage reports and [acceptance ledger](reports/acceptance.json).

## Run locally

From this repository, build and run any stage using its own folder. For the complete browser product:

```sh
docker build -t tablekeeper-stage4 ./stage-4
docker run --rm --name tablekeeper-stage4 --cpus 2 --memory 2g \
  -e PORT=8080 -p 127.0.0.1:8080:8080 tablekeeper-stage4
```

Open `http://127.0.0.1:8080/`; readiness is `GET /health`. The service starts empty. The official reset fixture supplies restaurant/account data through `POST /_test/reset`; fixture and API instructions are in each [RUN.md](stage-4/RUN.md) and the official specification. All scripts, styles, illustrations and timezone data are included locally. Runtime requires no external service, sibling folder or evidence directory.

On mounted macOS filesystems where generated AppleDouble xattrs prevent Docker from reading the directory, this equivalent committed-byte build context avoids that metadata:

```sh
git archive --format=tar HEAD:stage-4 | docker build -t tablekeeper-stage4 -
```

The application remains the same standalone stage folder. Evidence transport manifests verify its files against Git; neither source nor official tests are patched.

## Reproduce verification

Use the unchanged official checkout at `803560d2a678ace1414465c098eb0ab5380ffade`. From that checkout, run the harness against a fresh clone of this repository and a new output path:

```sh
python -m harness run --track tablekeeper --repo /absolute/fresh/clone \
  --all --mode isolated --out /absolute/new/evidence-directory
python -m harness check /absolute/fresh/clone --track tablekeeper
```

The first command builds all four folders independently and runs each cumulative suite plus the applicable next-stage probe. Required checks and expected probes must be reported separately. The second command checks package and room evidence; the authentic whole-room export is now included and passes the offline package check. Actual expanded commands, UTC timestamps, exits, logs and per-revision results are preserved in the evidence directory.

- [plan.md](plan.md) records the sequence and acceptance map.
- [FACTORY.md](FACTORY.md) records seat responsibilities, reproducibility, decisions, costs and failure handling.
- [reports/acceptance.json](reports/acceptance.json) records exact acceptance identities and per-revision counts.
- `mandates/` contains exact copies of the three supplied generic mandates.
- The four stage reports describe their exact gates: [1](reports/stage-1.md), [2](reports/stage-2.md), [3](reports/stage-3.md), [4](reports/stage-4.md).

Evidence is preserved at `/Volumes/FIGUEIRA/LABLAB/BAND DARK FACTORY/TABLEKEEPER/evidence/final-r03-20260927/agent-evidence`. This is the authorized run evidence location, not a runtime dependency. The final coordinator recorder is `coordinator/final_package_check.py`; it creates a new exact clone, records the package commit and stage trees, runs the unmodified all-folder isolated harness, checks the offline package and verifies tracked bytes remained unchanged. Actual final results belong to `coordinator/final-package-01/official/summary.json`, its four nested stage reports, and `coordinator/final-report.md` / `final-manifest.json`. The documentation is committed before that run; these external records bind the observed outcome to the exact complete package. A path or prepared script alone is not an execution result.

## Practical limits

State is ephemeral and uses one process with a transaction lock; separate replicas do not share bookings. The exact stage-4 planner supports the specified maximum of six tables, four declared pairs and six considered bookings; larger inputs return `planning_limit`. Idle confirmations do not poll; an explicit confirmation retrieval reads current state. Test controls and portable snapshots follow the challenge contract; exports contain synthetic credentials/tokens and remain private evidence. Targeted keyboard, mobile, contrast and browser checks are not a full accessibility certification.

## Scope and provenance

No previous submission source, historical room or product-specific bug report was input to this run. Official specifications and tests are not modified. Every agent commit is retained without amending, rebasing or squashing. Shipped official checks are partial conformance evidence, not proof of hidden-check correctness; next-stage probe failures are recorded separately from required suites.

The operator downloaded the authentic full BAND session after completion: `room.json` contains 3,154 events and exactly one human task message. Its original bytes are retained (SHA256 `860531f7e92c47ea06d80e32532eb415d6bfb105f8179a2ede475714aea4e5ce`). The offline package check passes. Public review reports and official results are in [reports/r03-evidence](reports/r03-evidence). This operator packaging adds evidence and documentation only; every accepted stage tree and all agent commits remain unchanged. Platform submission is a separate operator action.
