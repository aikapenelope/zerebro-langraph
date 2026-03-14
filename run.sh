#!/usr/bin/env bash
# Launch the cerebro meta-agent.
#
# Prerequisites:
#   1. Copy .env.example to .env and fill in your ANTHROPIC_API_KEY
#   2. Install deps: pip install -e ".[dev]"
#
# Usage:
#   ./run.sh              # starts Chainlit chat UI on localhost:8000
#   ./run.sh studio       # starts LangGraph dev server for LangSmith Studio
#   ./run.sh --port 3000  # Chainlit on custom port

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

MODE="${1:-chat}"

if [ "$MODE" = "studio" ]; then
    shift
    echo "Starting Cerebro via LangGraph Studio..."
    echo "  Connect LangSmith Studio to http://localhost:2024"
    echo "  Phoenix: http://localhost:${PHOENIX_PORT:-6006} (if enabled)"
    echo ""
    exec langgraph dev "$@"
else
    echo "Starting Cerebro chat UI..."
    echo "  UI: http://localhost:8000"
    echo "  Phoenix: http://localhost:${PHOENIX_PORT:-6006} (if enabled)"
    echo ""
    exec chainlit run app.py -w "$@"
fi
