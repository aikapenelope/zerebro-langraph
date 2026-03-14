"""Agent configuration schema.

Each agent is defined by a YAML config file stored in agents/configs/.
The meta-agent (cerebro) creates and modifies these configs via tools.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Default model for all agents (Haiku 4.5 via Anthropic)
DEFAULT_MODEL = "anthropic:claude-haiku-4-5"

# Inactive alternative (uncomment to switch)
# DEFAULT_MODEL = "openai:gpt-4o-mini"


@dataclass
class AgentConfig:
    """Configuration for a single agent managed by the cerebro."""

    name: str
    description: str = ""
    model: str = DEFAULT_MODEL
    system_prompt: str = ""
    mcp_servers: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for YAML storage."""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "mcp_servers": self.mcp_servers,
            "skills": self.skills,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentConfig:
        """Deserialize from a plain dict (loaded from YAML)."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            model=data.get("model", DEFAULT_MODEL),
            system_prompt=data.get("system_prompt", ""),
            mcp_servers=data.get("mcp_servers", []),
            skills=data.get("skills", []),
            enabled=data.get("enabled", True),
        )

    def summary(self) -> str:
        """Return a human-readable one-line summary."""
        status = "enabled" if self.enabled else "disabled"
        mcp_count = len(self.mcp_servers)
        return f"{self.name} ({status}) - model: {self.model}, MCP servers: {mcp_count}"
