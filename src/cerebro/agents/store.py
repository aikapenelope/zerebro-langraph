"""Agent config store: CRUD operations for agent YAML configs.

Agent configs are stored as individual YAML files in agents/configs/.
Each file is named {agent_name}.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cerebro.agents.config import AgentConfig

# Default directory for agent config files
_DEFAULT_CONFIGS_DIR = Path(__file__).parent / "configs"


def _configs_dir() -> Path:
    """Get the configs directory, creating it if needed."""
    _DEFAULT_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_CONFIGS_DIR


def _agent_path(name: str) -> Path:
    """Get the file path for an agent config."""
    # Sanitize name: lowercase, replace spaces with hyphens
    safe_name = name.lower().replace(" ", "-")
    return _configs_dir() / f"{safe_name}.yaml"


def save_agent(config: AgentConfig) -> str:
    """Save an agent config to disk.

    Args:
        config: The agent configuration to save.

    Returns:
        Path to the saved file as a string.
    """
    path = _agent_path(config.name)
    path.write_text(
        yaml.dump(config.to_dict(), default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return str(path)


def load_agent(name: str) -> AgentConfig | None:
    """Load an agent config from disk.

    Args:
        name: The agent name.

    Returns:
        AgentConfig if found, None otherwise.
    """
    path = _agent_path(name)
    if not path.exists():
        return None

    data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return AgentConfig.from_dict(data)


def delete_agent(name: str) -> bool:
    """Delete an agent config from disk.

    Args:
        name: The agent name.

    Returns:
        True if deleted, False if not found.
    """
    path = _agent_path(name)
    if not path.exists():
        return False
    path.unlink()
    return True


def list_agents() -> list[AgentConfig]:
    """List all saved agent configs.

    Returns:
        List of AgentConfig objects, sorted by name.
    """
    configs_dir = _configs_dir()
    agents: list[AgentConfig] = []
    for path in sorted(configs_dir.glob("*.yaml")):
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "name" in data:
            agents.append(AgentConfig.from_dict(data))
    return agents


def agent_exists(name: str) -> bool:
    """Check if an agent config exists.

    Args:
        name: The agent name.

    Returns:
        True if the agent config file exists.
    """
    return _agent_path(name).exists()
