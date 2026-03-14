"""Agent runner: instantiate and run agents from their YAML configs.

Loads an agent config, connects to its MCP servers to discover tools,
and creates a deepagents graph ready to handle messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph.state import CompiledStateGraph

from cerebro.agents.config import AgentConfig
from cerebro.agents.mcp_registry import load_registry
from cerebro.agents.store import load_agent

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ---------------------------------------------------------------------------
# MCP tool discovery
# ---------------------------------------------------------------------------


async def _discover_mcp_tools(
    server_names: list[str],
) -> list[BaseTool]:
    """Connect to MCP servers and return their tools.

    Args:
        server_names: Names of MCP servers from the registry.

    Returns:
        List of LangChain tools from the connected servers.
    """
    registry = load_registry()
    client_specs: dict[str, Any] = {}

    for name in server_names:
        cfg = registry.get(name)
        if cfg is None or not cfg.enabled:
            continue
        client_specs[name] = cfg.to_client_spec()

    if not client_specs:
        return []

    client = MultiServerMCPClient(client_specs)  # type: ignore[arg-type]
    return await client.get_tools()


# ---------------------------------------------------------------------------
# Agent instantiation
# ---------------------------------------------------------------------------


def _build_agent(
    config: AgentConfig,
    tools: list[BaseTool],
) -> CompiledStateGraph:
    """Build a deepagents graph from an agent config and its tools.

    Args:
        config: The agent configuration.
        tools: Pre-discovered tools (from MCP servers).

    Returns:
        A compiled LangGraph ready to process messages.
    """
    # Backend for default middleware stack (virtual mode avoids issue #1776)
    backend = FilesystemBackend(
        root_dir=str(_PROJECT_ROOT),
        virtual_mode=True,
    )

    # Collect skills (absolute paths per deepagents issue #934)
    skills: list[str] | None = None
    if config.skills:
        skills = [str(Path(s).resolve()) if not Path(s).is_absolute() else s for s in config.skills]

    # NOTE: No checkpointer. Child agents are ephemeral (one-shot invocations
    # from the run_agent tool). The langgraph API server manages persistence
    # for the parent cerebro graph; child agents don't need it.
    return create_deep_agent(
        model=config.model,
        tools=list(tools),
        system_prompt=config.system_prompt,
        checkpointer=None,
        backend=backend,
        skills=skills,
        name=config.name,
        debug=False,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_agent(agent_name: str) -> CompiledStateGraph:
    """Load an agent config, discover its MCP tools, and return a ready graph.

    Args:
        agent_name: Name of the agent (must exist in configs/).

    Returns:
        A compiled LangGraph for the agent.

    Raises:
        ValueError: If the agent is not found or is disabled.
    """
    config = load_agent(agent_name)
    if config is None:
        raise ValueError(f"Agent '{agent_name}' not found.")
    if not config.enabled:
        raise ValueError(f"Agent '{agent_name}' is disabled.")

    # Discover tools from MCP servers
    tools = await _discover_mcp_tools(config.mcp_servers)

    return _build_agent(config, tools)
