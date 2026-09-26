#!/usr/bin/env bash
# Operator-provided demonstration wrapper. Does not change any stage implementation.
set -euo pipefail
DEMO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO_PORT="${DEMO_PORT:-18080}"
DEMO_NAME="${DEMO_NAME:-tablekeeper-figueira-demo}"
DEMO_IMAGE="tablekeeper-figueira-demo:local"
case "$DEMO_PORT" in ''|*[!0-9]*) echo "DEMO_PORT must be numeric." >&2; exit 2;; esac
if docker container inspect "$DEMO_NAME" >/dev/null 2>&1; then
  echo "Container $DEMO_NAME already exists. Choose another DEMO_NAME or stop it explicitly." >&2
  exit 2
fi
docker build -t "$DEMO_IMAGE" "$DEMO_ROOT/stage-4"
DEMO_ID="$(docker run --detach --rm --name "$DEMO_NAME" --cpus=2 --memory=2g -p "127.0.0.1:$DEMO_PORT:8080" "$DEMO_IMAGE")"
DEMO_READY=0
for DEMO_TRY in $(seq 1 60); do
  if curl --fail --silent "http://127.0.0.1:$DEMO_PORT/health" >/dev/null; then DEMO_READY=1; break; fi
  sleep 1
done
if [ "$DEMO_READY" != 1 ]; then
  docker logs "$DEMO_ID" >&2
  docker stop "$DEMO_ID" >/dev/null
  echo "The demo did not become healthy within 60 seconds." >&2
  exit 1
fi
curl --fail --silent --show-error -X POST -H 'Content-Type: application/json' --data-binary "@$DEMO_ROOT/docs/demo-fixture.json" "http://127.0.0.1:$DEMO_PORT/_test/reset"
printf '\nOpen: http://127.0.0.1:%s\n' "$DEMO_PORT"
printf 'Synthetic login: ada@example.test / fixture-pass\n'
printf 'Choose a date and five guests to try combined tables.\n'
printf 'This is a local contest demo. Data is discarded when stopped.\n'
printf 'Stop your demo with: docker stop %s\n' "$DEMO_NAME"
