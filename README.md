# Figueira Dark Factory — Tablekeeper

Owner: Athos Figueiredo, Figueira, Brazil.

Competition track: Tablekeeper. This repository contains the Stage 1 JSON API produced by the three-seat Figueira BAND factory. Only Stage 1 is implemented.

The final API revision `0f96bf0cd889959d134ca6f8a5ee3066bbe459f8` passed all 120 shipped Stage 1 checks in the official isolated harness and all 27 independently authored review groups. The latter exercised 955 HTTP requests with no observed 5xx. These are local verification results, not official event acceptance or submission.

Build and run from the repository root:

```sh
docker build -t tablekeeper-stage-1 stage-1
docker run --rm --name tablekeeper-stage-1 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper-stage-1
```

`GET /health` returns `{"status":"ok"}`. No manual initialization or runtime external service is required. The image starts with empty state; the specified test fixture endpoint supplies users and restaurant configuration. State is intentionally ephemeral.

- [RUN.md](stage-1/RUN.md): standalone image, runtime behavior and focused test commands.
- [Stage 1 report](STAGE-1-REPORT.md): tested revision, results, repaired defects, evidence and limits.
- [Plan and acceptance map](plan.md): complete requirement decomposition and interpretations.
- [Factory](FACTORY.md) and [mandates](mandates/): reusable roles, collaboration and observed recovery.

There is no Stage 2 UI or later-stage implementation. The complete run evidence remains in the explicitly assigned local evidence directory identified in the report. No room export, public publication or event submission is claimed.
