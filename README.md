# Zerebro — Personal AI Meta-Agent

A **deepagents**-based meta-agent ("cerebro") that creates and manages other AI agents through natural language conversation, similar to twin.so's agent builder.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Chainlit UI (localhost:8000)                    │
│  ┌───────────────────────────────────────────┐   │
│  │  Cerebro (meta-agent)                     │   │
│  │  - Claude Haiku 4.5                       │   │
│  │  - SQLite checkpointer                    │   │
│  │  - SummarizationMiddleware                │   │
│  │  - 10 meta-tools (CRUD agents, MCP, etc.) │   │
│  └───────────┬───────────────────────────────┘   │
│              │ creates/manages                    │
│  ┌───────────▼───────────────────────────────┐   │
│  │  Agent Configs (YAML on disk)             │   │
│  │  - name, model, system_prompt             │   │
│  │  - mcp_servers, skills, enabled           │   │
│  └───────────┬───────────────────────────────┘   │
│              │ instantiated by runner             │
│  ┌───────────▼───────────────────────────────┐   │
│  │  Child Agents (deepagents graphs)         │   │
│  │  - MCP tools via HTTP transport           │   │
│  │  - Skills from markdown files             │   │
│  └───────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  MCP Servers (HTTP)  │
│  n8n · Remotion      │
│  Grafiti · mem0      │
└─────────────────────┘
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/aikapenelope/zerebro-langraph.git
cd zerebro-langraph
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Run

```bash
./run.sh
```

This starts the Chainlit chat UI on `http://localhost:8000`. Open it in your browser and start talking to the cerebro.

**Alternative: LangSmith Studio**

```bash
./run.sh studio
```

This starts the LangGraph dev server on `localhost:2024` for use with LangSmith Studio (free tier works).

## Usage

Talk to the cerebro in natural language:

- **"Create an agent called email-assistant that helps me draft professional emails"**
- **"List my agents"**
- **"Update email-assistant to also use the n8n MCP server"**
- **"What MCP servers are available?"**
- **"Add a new MCP server called my-api at http://localhost:8080/mcp"**
- **"Delete the email-assistant agent"**

## Project Structure

```
zerebro-langraph/
├── app.py                      # Chainlit chat UI entry point
├── chainlit.md                 # Chainlit welcome page
├── langgraph.json              # LangGraph Studio config
├── pyproject.toml              # Dependencies and tool config
├── run.sh                      # Convenience launcher
├── .env.example                # Environment template
└── src/cerebro/
    ├── graph.py                # LangGraph Studio entry point
    ├── agents/
    │   ├── cerebro.py          # Meta-agent factory (create_cerebro)
    │   ├── config.py           # AgentConfig dataclass
    │   ├── store.py            # YAML CRUD for agent configs
    │   ├── meta_tools.py       # 10 tools the cerebro uses
    │   ├── runner.py           # Instantiate agents from configs
    │   ├── mcp_registry.py     # MCP server registry
    │   ├── mcp_servers.yaml    # Pre-configured MCP servers
    │   └── configs/            # Agent YAML configs (created at runtime)
    ├── observability/
    │   └── phoenix_setup.py    # Optional Phoenix/OTel tracing
    ├── skills/                 # Skill markdown files
    └── memory/                 # Reserved for future memory features
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **deepagents** for all agents | Official LangChain meta-agent framework with middleware, skills, memory |
| **Claude Haiku 4.5** only | Cost-effective, fast, sufficient for agent management tasks |
| **Chainlit** for UI | Open-source chat UI, no external auth required, streaming support |
| **MCP HTTP transport** | Avoids stdio issues (deepagents #641, #1778) |
| **YAML configs on disk** | Simple, git-friendly, no database needed for agent definitions |
| **SQLite checkpointer** | Zero-config persistence for single user |
| **Phoenix optional** | Tracing is nice-to-have; system works without it |
| **LangSmith Studio optional** | Free tier available for graph visualization and debugging |

## MCP Servers

Pre-configured in `src/cerebro/agents/mcp_servers.yaml`:

| Server | Description | Env Var |
|--------|-------------|---------|
| n8n | Workflow automation | `MCP_N8N_URL` |
| remotion | Video generation | `MCP_REMOTION_URL` |
| grafiti | Knowledge graph | `MCP_GRAFITI_URL` |
| mem0 | Long-term memory | `MCP_MEM0_URL` |

Set the URLs in your `.env` file. Servers are only connected when an agent's config references them.

## Observability

Phoenix tracing is optional. When enabled, visit `http://localhost:6006` to see traces.

To disable: remove `arize-phoenix` and `openinference-instrumentation-langchain` from `pyproject.toml`. The system continues working without them.

## Development

```bash
# Type checking
pyright src/ app.py

# Linting
ruff check src/ app.py

# Formatting
ruff format src/ app.py
```

## Requirements

- Python >= 3.11
- Anthropic API key
- MCP servers running (for agents that use them)
