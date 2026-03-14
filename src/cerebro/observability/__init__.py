"""Observability setup with Phoenix (OTel tracing).

Phoenix is optional. If it fails to initialize (missing deps, version
conflicts, etc.), the system continues without tracing.
"""

from cerebro.observability.phoenix_setup import setup_observability

__all__ = ["setup_observability"]
