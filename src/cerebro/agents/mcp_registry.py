"""MCP server registry: discover, configure, and connect to MCP servers.

All MCP servers use HTTP transport (not stdio) for reliability.
See deepagents GitHub issue #641 and #1778 for why stdio is avoided.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

# Default path for the MCP servers registry file
_DEFAULT_REGISTRY_PATH = Path(__file__).parent / "mcp_servers.yaml"


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""

    name: str
    url: str
    description: str = ""
    transport: str = "http"
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_client_spec(self) -> dict[str, Any]:
        """Convert to the dict format expected by MultiServerMCPClient."""
        spec: dict[str, Any] = {
            "url": self.url,
            "transport": self.transport,
        }
        if self.headers:
            spec["headers"] = self.headers
        return spec


def load_registry(path: Path | None = None) -> dict[str, MCPServerConfig]:
    """Load MCP server configs from a YAML file.

    Environment variables in URLs are expanded (e.g., ${MCP_N8N_URL}).

    Args:
        path: Path to the YAML registry file. Defaults to mcp_servers.yaml
              next to this module.

    Returns:
        Dict mapping server name to its config.
    """
    registry_path = path or _DEFAULT_REGISTRY_PATH
    if not registry_path.exists():
        return {}

    raw = registry_path.read_text(encoding="utf-8")
    # Expand environment variables in the YAML content
    expanded = os.path.expandvars(raw)
    data = yaml.safe_load(expanded)

    if not isinstance(data, dict) or "servers" not in data:
        return {}

    servers: dict[str, MCPServerConfig] = {}
    for entry in data["servers"]:
        name = entry["name"]
        servers[name] = MCPServerConfig(
            name=name,
            url=entry["url"],
            description=entry.get("description", ""),
            transport=entry.get("transport", "http"),
            headers=entry.get("headers", {}),
            enabled=entry.get("enabled", True),
        )
    return servers


def save_registry(
    servers: dict[str, MCPServerConfig],
    path: Path | None = None,
) -> None:
    """Save MCP server configs to a YAML file.

    Args:
        servers: Dict mapping server name to its config.
        path: Path to write. Defaults to mcp_servers.yaml next to this module.
    """
    registry_path = path or _DEFAULT_REGISTRY_PATH
    entries = []
    for cfg in servers.values():
        entry: dict[str, Any] = {
            "name": cfg.name,
            "url": cfg.url,
            "description": cfg.description,
            "transport": cfg.transport,
            "enabled": cfg.enabled,
        }
        if cfg.headers:
            entry["headers"] = cfg.headers
        entries.append(entry)

    registry_path.write_text(
        yaml.dump({"servers": entries}, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


async def get_mcp_tools(server_names: list[str]) -> list[BaseTool]:
    """Connect to the specified MCP servers and return their tools.

    Only connects to servers that are enabled in the registry.

    Args:
        server_names: List of server names to connect to.

    Returns:
        List of LangChain tools discovered from the MCP servers.
    """
    registry = load_registry()
    client_specs: dict[str, Any] = {}

    for name in server_names:
        cfg = registry.get(name)
        if cfg is None:
            continue
        if not cfg.enabled:
            continue
        client_specs[name] = cfg.to_client_spec()

    if not client_specs:
        return []

    client = MultiServerMCPClient(client_specs)  # type: ignore[arg-type]
    tools: list[BaseTool] = await client.get_tools()
    return tools


def list_available_servers() -> list[dict[str, Any]]:
    """List all registered MCP servers with their status.

    Returns:
        List of dicts with server info (name, url, description, enabled).
    """
    registry = load_registry()
    return [
        {
            "name": cfg.name,
            "url": cfg.url,
            "description": cfg.description,
            "enabled": cfg.enabled,
        }
        for cfg in registry.values()
    ]
