# Try the actual service locally

This demonstration uses the unchanged, independently reviewed Stage 4 service in its own container. The helper and fixture are presentation materials prepared outside the autonomous implementation.

With Docker running, from the repository root:

```sh
bash docs/run-demo.sh
```

Open the printed local URL. Sign in as **ada@example.test** with the synthetic password **fixture-pass**. Select The Fern Room, a date, and five guests. Choose the Garden booth + Window table pair, confirm, and repeat the unchanged request: the confirmation reference stays the same. Open **Your reservation** to retrieve or cancel it. Use a future date if you intend to cancel, because the restaurant's cancellation cutoff applies.

The fixture contains no real guest or booking. The page shows the restaurant's local time. Re-running the helper with another `DEMO_NAME` and `DEMO_PORT` creates a separate instance; it does not overwrite an existing container. Stop the named demo when finished.

The helper binds only to 127.0.0.1. It is a demonstration, not the isolated grading check. The contest service intentionally exposes unauthenticated test controls and keeps ephemeral state; do not use it as a public service or for real customer records. The official reproduction commands and runtime contract remain in each stage's RUN.md.
