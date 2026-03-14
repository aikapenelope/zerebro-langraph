#!/usr/bin/env bash
# Launch the cerebro meta-agent via LangGraph Studio.
#
# Prerequisites:
#   1. Copy .env.example to .env and fill in your ANTHROPIC_API_KEY
#   2. Install deps: pip install -e ".[dev]"
#
# Usage:
#   ./run.sh          # starts LangGraph dev server on localhost:2024
#   ./run.sh --port 3000  # custom port

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if present
if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# Load .env if present
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

echo "Starting Cerebro via LangGraph Studio..."
echo "  UI: http://localhost:2024 (connect via LangGraph Studio desktop app)"
echo "  Phoenix: http://localhost:${PHOENIX_PORT:-6006} (if enabled)"
echo ""

exec langgraph dev "$@"
