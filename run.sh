#!/usr/bin/env bash
# Helper script to run common development workflows.
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

COMMAND="${1:-dev}"
if [ "$#" -gt 0 ]; then
    shift
fi
ARGS=("$@")

usage() {
    cat <<'USAGE'
Usage: ./run.sh [command] [args...]

Commands:
  dev       Start the FastAPI dev server (default)
  test      Run pytest; extra args are forwarded
  lint      Run style and type checks (black --check, flake8, mypy)
  format    Format code with black
  docker    Launch docker-compose in the foreground
  help      Show this help message

Environment:
  HOST / PORT   Override dev server bind address (default 127.0.0.1:8000)
  FORCE_POETRY_INSTALL=1   Force dependency installation via Poetry
  SKIP_POETRY_INSTALL=1    Skip the automatic Poetry install step
USAGE
}

ensure_poetry() {
    if ! command -v poetry >/dev/null 2>&1; then
        echo "Poetry is required to run this command. Install it from https://python-poetry.org/docs/" >&2
        exit 1
    fi
}

ensure_dependencies() {
    if [[ "${SKIP_POETRY_INSTALL:-0}" == "1" ]]; then
        return
    fi

    if [[ "${FORCE_POETRY_INSTALL:-0}" == "1" ]]; then
        echo "Installing dependencies (forced) via Poetry..."
        poetry install --no-interaction --sync
        return
    fi

    if ! poetry env info --path >/dev/null 2>&1; then
        echo "Installing dependencies via Poetry..."
        poetry install --no-interaction --sync
    fi
}

prepare_runtime_assets() {
    mkdir -p data/db data/backups

    if [ ! -f data/Corefile ]; then
        if [ -f docker/Corefile ]; then
            cp docker/Corefile data/Corefile
        else
            cat > data/Corefile <<'COREFILE'
. {
    forward . 223.5.5.5
    log
    errors
}
COREFILE
        fi
    fi
}

run_dev() {
    local host="${HOST:-127.0.0.1}"
    local port="${PORT:-8003}"
    poetry run uvicorn app.main:app --host "$host" --port "$port" --reload "$@"
}

run_test() {
    poetry run pytest "$@"
}

run_lint() {
    poetry run black --check app tests
    poetry run flake8 app tests
    poetry run mypy app
}

run_format() {
    poetry run black app tests
}

run_docker() {
    prepare_runtime_assets
    docker-compose up "$@"
}

case "$COMMAND" in
    dev)
        ensure_poetry
        ensure_dependencies
        prepare_runtime_assets
        run_dev "${ARGS[@]}"
        ;;
    test)
        ensure_poetry
        ensure_dependencies
        run_test "${ARGS[@]}"
        ;;
    lint)
        ensure_poetry
        ensure_dependencies
        run_lint
        ;;
    format)
        ensure_poetry
        ensure_dependencies
        run_format
        ;;
    docker)
        run_docker "${ARGS[@]}"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Unknown command: $COMMAND" >&2
        usage
        exit 1
        ;;
esac
