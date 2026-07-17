#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env.example"
if [[ -f ".env" ]]; then
  ENV_FILE=".env"
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

mkdir -p reports
find reports -maxdepth 1 -type f ! -name '.gitkeep' -delete
COMPOSE=(docker compose --env-file "$ENV_FILE")
functional_exit=0
load_exit=0
quality_exit=0

cleanup() {
  "${COMPOSE[@]}" logs --no-color sut > reports/service.log 2>&1 || true
  "${COMPOSE[@]}" down --volumes --remove-orphans || true
}
trap cleanup EXIT INT TERM

"${COMPOSE[@]}" pull sut
"${COMPOSE[@]}" build test-runner

"${COMPOSE[@]}" run --rm test-runner sh -c \
  'ruff format --check src tests load && ruff check src tests load && mypy src' \
  || quality_exit=$?

"${COMPOSE[@]}" up --detach sut

if ! "${COMPOSE[@]}" run --rm test-runner python -m automation_assignment wait-for-api; then
  echo "Service readiness failed; functional and load gates cannot run."
  "${COMPOSE[@]}" run --rm test-runner python -m automation_assignment write-summary \
    --quality-exit "$quality_exit" --functional-exit 1 --load-exit 1 || true
  exit 1
fi

"${COMPOSE[@]}" run --rm test-runner pytest tests \
  --html=reports/pytest-report.html \
  --self-contained-html \
  --junitxml=reports/junit.xml || functional_exit=$?

"${COMPOSE[@]}" run --rm \
  --env LOAD_MIN_SUCCESSFUL_REQUESTS=1 \
  test-runner locust \
  --locustfile load/locustfile.py \
  --headless \
  --users 5 \
  --spawn-rate 5 \
  --run-time "${LOAD_WARMUP_SECONDS:-5}s" || true

sut_id="$("${COMPOSE[@]}" ps --quiet sut)"
if [[ -n "$sut_id" ]]; then
  docker stats --no-stream "$sut_id" > reports/docker-stats-before-load.txt || true
fi

"${COMPOSE[@]}" run --rm test-runner locust \
  --locustfile load/locustfile.py \
  --headless \
  --users "${LOAD_USERS:-25}" \
  --spawn-rate "${LOAD_SPAWN_RATE:-25}" \
  --run-time "${LOAD_DURATION_SECONDS:-60}s" \
  --html reports/locust-report.html \
  --csv reports/locust_stats || load_exit=$?

if [[ -n "$sut_id" ]]; then
  docker stats --no-stream "$sut_id" > reports/docker-stats-after-load.txt || true
fi

"${COMPOSE[@]}" run --rm test-runner python -m automation_assignment write-summary \
  --quality-exit "$quality_exit" \
  --functional-exit "$functional_exit" \
  --load-exit "$load_exit"
