"""Meta-agent tools: the toolbox the cerebro uses to manage agents.

These tools are passed to the cerebro's create_deep_agent() call.
They provide CRUD operations for agent configs, MCP server management,
and the ability to run child agents.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from cerebro.agents.config import DEFAULT_MODEL, AgentConfig
from cerebro.agents.mcp_registry import (
    MCPServerConfig,
    list_available_servers,
    load_registry,
    save_registry,
)
from cerebro.agents.store import (
    agent_exists,
    load_agent,
    save_agent,
)
from cerebro.agents.store import (
    delete_agent as _delete_agent,
)
from cerebro.agents.store import (
    list_agents as _list_agents,
)

# ---------------------------------------------------------------------------
# Agent CRUD tools
# ---------------------------------------------------------------------------


@tool
def create_agent_config(
    name: str,
    description: str,
    system_prompt: str,
    mcp_servers: list[str] | None = None,
    skills: list[str] | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Create a new agent configuration.

    Args:
        name: Unique name for the agent (e.g. "email-assistant").
        description: What this agent does.
        system_prompt: The system prompt that defines the agent's behavior.
        mcp_servers: Optional list of MCP server names to connect to.
        skills: Optional list of skill file paths.
        model: LLM model in "provider:model" format. Defaults to Claude Haiku 4.5.

    Returns:
        JSON string with the created agent summary and file path.
    """
    if agent_exists(name):
        return json.dumps(
            {"error": f"Agent '{name}' already exists. Use update_agent_config to modify it."}
        )

    config = AgentConfig(
        name=name,
        description=description,
        model=model,
        system_prompt=system_prompt,
        mcp_servers=mcp_servers or [],
        skills=skills or [],
        enabled=True,
    )
    path = save_agent(config)
    return json.dumps({"status": "created", "agent": config.summary(), "path": path})


@tool
def update_agent_config(
    name: str,
    description: str | None = None,
    system_prompt: str | None = None,
    mcp_servers: list[str] | None = None,
    skills: list[str] | None = None,
    model: str | None = None,
    enabled: bool | None = None,
) -> str:
    """Update an existing agent configuration.

    Only the provided fields are updated; others remain unchanged.

    Args:
        name: Name of the agent to update.
        description: New description (optional).
        system_prompt: New system prompt (optional).
        mcp_servers: New list of MCP server names (optional, replaces existing).
        skills: New list of skill file paths (optional, replaces existing).
        model: New model in "provider:model" format (optional).
        enabled: Enable or disable the agent (optional).

    Returns:
        JSON string with the updated agent summary.
    """
    config = load_agent(name)
    if config is None:
        return json.dumps({"error": f"Agent '{name}' not found."})

    if description is not None:
        config.description = description
    if system_prompt is not None:
        config.system_prompt = system_prompt
    if mcp_servers is not None:
        config.mcp_servers = mcp_servers
    if skills is not None:
        config.skills = skills
    if model is not None:
        config.model = model
    if enabled is not None:
        config.enabled = enabled

    save_agent(config)
    return json.dumps({"status": "updated", "agent": config.summary()})


@tool
def list_agents() -> str:
    """List all configured agents.

    Returns:
        JSON array of agent summaries.
    """
    agents = _list_agents()
    if not agents:
        return json.dumps({"agents": [], "message": "No agents configured yet."})
    return json.dumps({"agents": [a.to_dict() for a in agents]})


@tool
def get_agent_config(name: str) -> str:
    """Get the full configuration of a specific agent.

    Args:
        name: Name of the agent.

    Returns:
        JSON string with the full agent config or an error.
    """
    config = load_agent(name)
    if config is None:
        return json.dumps({"error": f"Agent '{name}' not found."})
    return json.dumps(config.to_dict())


@tool
def delete_agent_config(name: str) -> str:
    """Delete an agent configuration.

    Args:
        name: Name of the agent to delete.

    Returns:
        JSON string confirming deletion or error.
    """
    if _delete_agent(name):
        return json.dumps({"status": "deleted", "agent": name})
    return json.dumps({"error": f"Agent '{name}' not found."})


# ---------------------------------------------------------------------------
# MCP server management tools
# ---------------------------------------------------------------------------


@tool
def list_mcp_servers() -> str:
    """List all registered MCP servers and their status.

    Returns:
        JSON array of MCP server info.
    """
    servers = list_available_servers()
    return json.dumps({"servers": servers})


@tool
def add_mcp_server(
    name: str,
    url: str,
    description: str = "",
    transport: str = "http",
) -> str:
    """Register a new MCP server in the registry.

    Args:
        name: Unique name for the server (e.g. "n8n").
        url: HTTP URL of the MCP server endpoint.
        description: What this server provides.
        transport: Transport type, always "http" for reliability.

    Returns:
        JSON string confirming the server was added.
    """
    registry = load_registry()
    if name in registry:
        return json.dumps(
            {"error": f"MCP server '{name}' already exists. Remove it first to re-add."}
        )

    registry[name] = MCPServerConfig(
        name=name,
        url=url,
        description=description,
        transport=transport,
        enabled=True,
    )
    save_registry(registry)
    return json.dumps({"status": "added", "server": name, "url": url})


@tool
def remove_mcp_server(name: str) -> str:
    """Remove an MCP server from the registry.

    Args:
        name: Name of the server to remove.

    Returns:
        JSON string confirming removal or error.
    """
    registry = load_registry()
    if name not in registry:
        return json.dumps({"error": f"MCP server '{name}' not found in registry."})

    del registry[name]
    save_registry(registry)
    return json.dumps({"status": "removed", "server": name})


# ---------------------------------------------------------------------------
# Skill management tools
# ---------------------------------------------------------------------------


@tool
def add_skill_to_agent(agent_name: str, skill_path: str) -> str:
    """Add a skill file to an agent's configuration.

    Skills are markdown files that teach the agent specific capabilities.
    Use absolute paths to avoid deepagents issue #934.

    Args:
        agent_name: Name of the agent.
        skill_path: Absolute path to the skill markdown file.

    Returns:
        JSON string confirming the skill was added.
    """
    config = load_agent(agent_name)
    if config is None:
        return json.dumps({"error": f"Agent '{agent_name}' not found."})

    if skill_path in config.skills:
        return json.dumps({"status": "already_present", "skill": skill_path})

    config.skills.append(skill_path)
    save_agent(config)
    return json.dumps({"status": "added", "agent": agent_name, "skill": skill_path})


@tool
def remove_skill_from_agent(agent_name: str, skill_path: str) -> str:
    """Remove a skill file from an agent's configuration.

    Args:
        agent_name: Name of the agent.
        skill_path: Path of the skill to remove.

    Returns:
        JSON string confirming removal or error.
    """
    config = load_agent(agent_name)
    if config is None:
        return json.dumps({"error": f"Agent '{agent_name}' not found."})

    if skill_path not in config.skills:
        return json.dumps({"error": f"Skill '{skill_path}' not found in agent '{agent_name}'."})

    config.skills.remove(skill_path)
    save_agent(config)
    return json.dumps({"status": "removed", "agent": agent_name, "skill": skill_path})


# ---------------------------------------------------------------------------
# Agent execution tool
# ---------------------------------------------------------------------------


@tool
async def run_agent(agent_name: str, message: str) -> str:
    """Run a child agent and return its response.

    Instantiates the agent from its YAML config, sends it a message,
    and collects the full response. The child agent has access to its
    configured MCP tools and skills.

    Args:
        agent_name: Name of the agent to run (must exist and be enabled).
        message: The user message to send to the agent.

    Returns:
        JSON string with the agent's response text, or an error.
    """
    from cerebro.agents.runner import run_agent as _run_agent_graph

    try:
        graph = await _run_agent_graph(agent_name)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})

    # Each invocation gets a unique thread so child state is isolated.
    thread_id = f"{agent_name}-{uuid.uuid4().hex[:8]}"
    config = RunnableConfig(configurable={"thread_id": thread_id})

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )
    except Exception as exc:
        return json.dumps({"error": f"Agent '{agent_name}' failed: {exc}"})

    # Extract the last AI message from the result.
    messages = result.get("messages", [])
    ai_messages = [m for m in messages if isinstance(m, AIMessage) and m.content]
    if ai_messages:
        response_text = ai_messages[-1].content
    else:
        response_text = "(Agent produced no text response)"

    # Ensure response_text is a string (content can be str or list of blocks).
    if isinstance(response_text, list):
        response_text = "\n".join(
            block.get("text", str(block)) if isinstance(block, dict) else str(block)
            for block in response_text
        )

    return json.dumps(
        {
            "agent": agent_name,
            "response": response_text,
            "thread_id": thread_id,
        }
    )


# ---------------------------------------------------------------------------
# Collected tools list for the meta-agent
# ---------------------------------------------------------------------------


def get_meta_tools() -> list[Any]:
    """Return all meta-agent tools as a list for create_deep_agent()."""
    return [
        create_agent_config,
        update_agent_config,
        list_agents,
        get_agent_config,
        delete_agent_config,
        list_mcp_servers,
        add_mcp_server,
        remove_mcp_server,
        add_skill_to_agent,
        remove_skill_from_agent,
        run_agent,
    ]
