"""Cerebro meta-agent: creates and manages other agents via natural language.

The cerebro is a deepagents-based meta-agent whose tools are CRUD operations
on agent configs. When a user says "create an agent that does X", the cerebro
writes a YAML config to disk. When the user says "run agent Y", the cerebro
delegates to the agent runner which instantiates the agent from its config.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.state import CompiledStateGraph

from cerebro.agents.config import DEFAULT_MODEL
from cerebro.agents.meta_tools import get_meta_tools

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DB_PATH = _PROJECT_ROOT / "cerebro.db"
_SKILLS_DIR = _PROJECT_ROOT / "src" / "cerebro" / "skills"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

CEREBRO_PROMPT = """\
You are **Cerebro**, a personal meta-agent that creates and manages other AI \
agents through natural language conversation.

## Your capabilities

You have tools to:
- **Create** new agents with a name, description, system prompt, and optional \
MCP server connections.
- **List** all agents you have created.
- **View** the full configuration of any agent.
- **Update** an agent's config (prompt, model, MCP servers, skills, enabled).
- **Delete** agents you no longer need.
- **Manage MCP servers**: list available servers, add new ones, remove old ones.
- **Manage skills**: add or remove skill files from agents.

## How agent creation works

When the user asks you to create an agent:
1. Ask clarifying questions if the request is vague (what should the agent do? \
which MCP servers does it need?).
2. Craft a clear, detailed system prompt for the new agent.
3. Call `create_agent_config` with the name, description, system prompt, and \
any MCP servers the agent should connect to.
4. Confirm to the user what you created and how to use it.

## Available MCP servers

Call `list_mcp_servers` to see what MCP servers are registered. Each server \
provides tools the agent can use. Current servers include:
- **n8n**: Workflow automation (triggers, webhooks, integrations)
- **remotion**: Programmatic video generation
- **grafiti**: Knowledge graph operations (entities, relations, search)
- **mem0**: Long-term memory storage and retrieval

## Model

All agents use Claude Haiku 4.5 (`anthropic:claude-haiku-4-5`) by default. \
You can specify a different model when creating or updating an agent.

## Guidelines

- Be conversational and helpful, like twin.so's agent builder.
- When creating agents, write thorough system prompts that clearly define the \
agent's role, capabilities, and constraints.
- Suggest MCP server connections that match the agent's purpose.
- Use descriptive agent names (e.g., "email-assistant", "data-analyst").
- Keep the user informed about what you're doing at each step.
"""

# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_cerebro() -> CompiledStateGraph:
    """Create and return the cerebro meta-agent as a compiled LangGraph.

    The graph is configured with:
    - Claude Haiku 4.5 as the LLM
    - Meta-tools for agent CRUD, MCP management, and skill management
    - SQLite checkpointer for conversation persistence
    - FilesystemBackend in virtual mode (no real shell, avoids issue #1776)
    - Default middleware stack (TodoList, Filesystem, SubAgent,
      Summarization, AnthropicPromptCaching, PatchToolCalls)

    Returns:
        A CompiledStateGraph ready to be served by LangGraph Studio.
    """
    # Checkpointer: SQLite file next to the project root
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    checkpointer = SqliteSaver(conn=conn)
    checkpointer.setup()

    # Backend for middleware (virtual mode avoids stdin hang, issue #1776).
    # Passed to create_deep_agent so the default middleware stack
    # (including SummarizationMiddleware) uses it instead of StateBackend.
    backend = FilesystemBackend(
        root_dir=str(_PROJECT_ROOT),
        virtual_mode=True,
    )

    # Collect skills if any exist
    skills: list[str] | None = None
    if _SKILLS_DIR.exists():
        skill_files = sorted(_SKILLS_DIR.glob("*.md"))
        if skill_files:
            # Use absolute paths to avoid deepagents issue #934
            skills = [str(f.resolve()) for f in skill_files]

    return create_deep_agent(
        model=DEFAULT_MODEL,
        tools=get_meta_tools(),
        system_prompt=CEREBRO_PROMPT,
        checkpointer=checkpointer,
        backend=backend,
        skills=skills,
        name="cerebro",
        debug=False,
    )
