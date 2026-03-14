#!/usr/bin/env bash
# Launch the cerebro meta-agent backend.
#
# Prerequisites:
#   1. Copy .env.example to .env and fill in ANTHROPIC_API_KEY + LANGSMITH_API_KEY
#   2. Install deps: pip install -e ".[dev]"
#
# Usage:
#   ./run.sh          # starts LangGraph dev server on localhost:2024
#
# Then in a separate terminal, start the deep-agents-ui frontend:
#   cd deep-agents-ui && yarn dev
#   Open http://localhost:3000 and set Deployment URL = http://localhost:2024, Assistant ID = cerebro

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

echo "Starting Cerebro backend (LangGraph dev server)..."
echo "  API: http://localhost:2024"
echo "  Phoenix: http://localhost:${PHOENIX_PORT:-6006} (if enabled)"
echo ""
echo "  Frontend: start deep-agents-ui separately (yarn dev → http://localhost:3000)"
echo "  Set Deployment URL = http://localhost:2024, Assistant ID = cerebro"
echo ""
exec langgraph dev "$@"
