# Zerebro — Personal AI Meta-Agent

A **deepagents**-based meta-agent ("cerebro") that creates and manages other AI agents through natural language conversation, similar to twin.so's agent builder.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  deep-agents-ui (localhost:3000)                     │
│  ┌────────────────────────────────────────────────┐  │
│  │  Files panel · Todo list · Tool calls          │  │
│  │  Sub-agent indicators · Debug mode             │  │
│  │  Tool approval (approve/reject/edit)           │  │
│  └────────────────────┬───────────────────────────┘  │
│                       │ LangGraph SDK                 │
│  ┌────────────────────▼───────────────────────────┐  │
│  │  langgraph dev (localhost:2024)                 │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │  Cerebro (meta-agent)                    │  │  │
│  │  │  - Claude Haiku 4.5                      │  │  │
│  │  │  - SQLite checkpointer                   │  │  │
│  │  │  - 20 tools (9 built-in + 11 meta-tools) │  │  │
│  │  └──────────┬───────────────────────────────┘  │  │
│  │             │ creates/manages/runs              │  │
│  │  ┌──────────▼───────────────────────────────┐  │  │
│  │  │  Child Agents (deepagents graphs)        │  │  │
│  │  │  - MCP tools via HTTP transport          │  │  │
│  │  │  - Skills from markdown files            │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  MCP Servers (HTTP)  │
│  n8n · Remotion      │
│  Grafiti · mem0      │
└─────────────────────┘
```

## Quick Start (Docker — recommended for Windows)

### 1. Get your API keys

You need two keys. Both go in the `.env` file:

| Key | Where to get it | What it looks like |
|-----|----------------|--------------------|
| **ANTHROPIC_API_KEY** | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) | `sk-ant-api03-...` |
| **LANGSMITH_API_KEY** | [smith.langchain.com/settings](https://smith.langchain.com/settings) (free tier) | `lsv2_pt_...` |

### 2. Clone and configure

```bash
git clone https://github.com/aikapenelope/zerebro-langraph.git
cd zerebro-langraph
cp .env.example .env
```

Edit `.env` and paste your two keys:

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-real-key-here
LANGSMITH_API_KEY=lsv2_pt_your-real-key-here
```

### 3. Run

```bash
docker compose up
```

Wait for both services to start (first run downloads dependencies, takes ~2-3 min).

### 4. Open the UI

Go to **http://localhost:3000** and configure:
- **Deployment URL**: `http://localhost:2024`
- **Assistant ID**: `cerebro`
- **LangSmith API Key**: your `lsv2_pt_...` key

Done. Start talking to the cerebro.

## Quick Start (local — Mac/Linux)

<details>
<summary>Click to expand local setup instructions</summary>

### 1. Install backend

```bash
git clone https://github.com/aikapenelope/zerebro-langraph.git
cd zerebro-langraph
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" "langgraph-cli[inmem]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and LANGSMITH_API_KEY
```

### 3. Start backend

```bash
./run.sh
```

### 4. Start frontend (separate terminal)

```bash
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui
yarn install
yarn dev
```

Open `http://localhost:3000` and configure:
- **Deployment URL**: `http://localhost:2024`
- **Assistant ID**: `cerebro`
- **LangSmith API Key**: your `lsv2_pt_...` key

</details>

## Usage

Talk to the cerebro in natural language:

- **"Create an agent called email-assistant that helps me draft professional emails"**
- **"List my agents"**
- **"Update email-assistant to also use the n8n MCP server"**
- **"Run email-assistant with: draft a follow-up email to the client"**
- **"What MCP servers are available?"**
- **"Add a new MCP server called my-api at http://localhost:8080/mcp"**
- **"Delete the email-assistant agent"**

The deep-agents-ui shows:
- **Files panel**: view/edit files the agent creates in its virtual filesystem
- **Todo list**: visual task tracking with pending/in-progress/done states
- **Tool calls**: expandable boxes showing each tool's args and results
- **Sub-agent indicators**: see when child agents are running
- **Tool approval**: approve, reject, or edit tool calls before execution (when using `interrupt_on`)
- **Debug mode**: step-by-step execution with re-run capability

## Project Structure

```
zerebro-langraph/
├── Dockerfile                  # Backend container (langgraph dev)
├── docker-compose.yml          # Both services: backend + frontend
├── langgraph.json              # LangGraph config (graphs.cerebro)
├── pyproject.toml              # Dependencies and tool config
├── run.sh                      # Local backend launcher
├── .env.example                # Environment template (keys go here)
└── src/cerebro/
    ├── graph.py                # Entry point (Phoenix + cerebro init)
    ├── agents/
    │   ├── cerebro.py          # Meta-agent factory (create_cerebro)
    │   ├── config.py           # AgentConfig dataclass
    │   ├── store.py            # YAML CRUD for agent configs
    │   ├── meta_tools.py       # 11 meta-tools (CRUD + run_agent)
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
| **deep-agents-ui** | Official deepagents frontend with native file/todo/sub-agent/debug support |
| **MCP HTTP transport** | Avoids stdio issues (deepagents #641, #1778) |
| **YAML configs on disk** | Simple, git-friendly, no database needed for agent definitions |
| **SQLite checkpointer** | Zero-config persistence for single user |
| **LangSmith free tier** | Required for `langgraph dev` + SDK; free tier sufficient for personal use |
| **Docker Compose** | One command to run everything on any OS (Windows, Mac, Linux) |

## MCP Servers

Pre-configured in `src/cerebro/agents/mcp_servers.yaml`:

| Server | Description | Env Var |
|--------|-------------|---------|
| n8n | Workflow automation | `MCP_N8N_URL` |
| remotion | Video generation | `MCP_REMOTION_URL` |
| grafiti | Knowledge graph | `MCP_GRAFITI_URL` |
| mem0 | Long-term memory | `MCP_MEM0_URL` |

Set the URLs in your `.env` file. Servers are only connected when an agent's config references them.

If your MCP servers run on the host machine (not in Docker), use `host.docker.internal` instead of `localhost` in the URLs:

```env
MCP_N8N_URL=http://host.docker.internal:5678/mcp
```

## Observability

Phoenix tracing is optional. When enabled, visit `http://localhost:6006` to see traces.

To disable: remove `arize-phoenix` and `openinference-instrumentation-langchain` from `pyproject.toml`. The system continues working without them.

## Development

```bash
# Type checking
pyright src/

# Linting
ruff check src/

# Formatting
ruff format src/
```

## Requirements

**Docker (Windows/Mac/Linux):**
- Docker Desktop
- Anthropic API key
- LangSmith API key (free tier)

**Local (Mac/Linux):**
- Python >= 3.11
- Node.js + yarn (for deep-agents-ui frontend)
- Anthropic API key
- LangSmith API key (free tier)
