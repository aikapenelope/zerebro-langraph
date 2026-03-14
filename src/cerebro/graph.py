"""LangGraph Studio entry point.

This module exposes the compiled cerebro graph for use with ``langgraph dev``.
Phoenix tracing is initialized at import time (optional, degrades gracefully).
"""

from cerebro.agents.cerebro import create_cerebro
from cerebro.observability import setup_observability

# Initialize Phoenix tracing (no-op if deps are missing or broken)
setup_observability()

# Exposed to langgraph.json as "cerebro"
cerebro = create_cerebro()
