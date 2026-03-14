"""Phoenix observability setup for LangChain tracing.

Initializes Arize Phoenix as a local OTel collector and instruments
LangChain via openinference. This is entirely optional — if Phoenix
or its dependencies fail to load, the system runs without tracing.

Usage:
    from cerebro.observability import setup_observability
    setup_observability()  # call once at startup
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_initialized = False


def setup_observability() -> bool:
    """Start Phoenix and instrument LangChain.

    The Phoenix port is controlled by the PHOENIX_PORT env var (default 6006).

    If Phoenix starts successfully and the user has not explicitly set
    LANGSMITH_TRACING, it is defaulted to "false" to avoid sending
    duplicate traces to both Phoenix and LangSmith.

    Returns:
        True if Phoenix started successfully, False otherwise.
    """
    global _initialized  # noqa: PLW0603
    if _initialized:
        return True

    phoenix_port = os.environ.setdefault("PHOENIX_PORT", "6006")

    try:
        import phoenix as px
        from openinference.instrumentation.langchain import LangChainInstrumentor

        # Phoenix reads PHOENIX_PORT from env (no port= arg needed)
        px.launch_app()
        LangChainInstrumentor().instrument()
        _initialized = True

        # Only default LANGSMITH_TRACING to false when Phoenix is active.
        # If the user explicitly set LANGSMITH_TRACING=true in .env, respect it.
        os.environ.setdefault("LANGSMITH_TRACING", "false")

        logger.info("Phoenix tracing active on http://localhost:%s", phoenix_port)
        return True

    except ImportError:
        logger.warning(
            "Phoenix or openinference not installed. "
            "Run: pip install arize-phoenix openinference-instrumentation-langchain"
        )
        return False

    except Exception:
        logger.warning("Phoenix failed to start — continuing without tracing", exc_info=True)
        return False
