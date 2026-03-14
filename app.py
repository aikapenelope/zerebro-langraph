"""Chainlit UI for the Cerebro meta-agent.

Run with: chainlit run app.py -w
"""

from __future__ import annotations

import os

# Disable LangSmith tracing before any LangChain imports
os.environ.setdefault("LANGSMITH_TRACING", "false")

import chainlit as cl  # noqa: E402
from langchain_core.messages import AIMessageChunk, HumanMessage  # noqa: E402
from langchain_core.runnables import RunnableConfig  # noqa: E402

from cerebro.agents.cerebro import create_cerebro  # noqa: E402
from cerebro.observability import setup_observability  # noqa: E402

# Initialize observability (optional, degrades gracefully)
setup_observability()

# Create the cerebro graph once at module level
cerebro = create_cerebro()


@cl.on_chat_start
async def on_chat_start() -> None:
    """Welcome the user when a new chat session starts."""
    await cl.Message(
        content=(
            "**Cerebro** ready. I can create and manage AI agents for you.\n\n"
            "Try:\n"
            '- "Create an agent called email-assistant that drafts professional emails"\n'
            '- "List my agents"\n'
            '- "What MCP servers are available?"\n'
        ),
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Handle incoming user messages with streaming."""
    # Use the Chainlit session ID as the LangGraph thread_id for persistence
    config = RunnableConfig(
        configurable={"thread_id": cl.context.session.id},
        callbacks=[cl.LangchainCallbackHandler()],
    )

    response = cl.Message(content="")

    # Stream the graph output using "messages" mode for token-level streaming
    async for event, metadata in cerebro.astream(
        {"messages": [HumanMessage(content=message.content)]},
        config=config,
        stream_mode="messages",
    ):
        # Only stream AI message content (skip tool calls, human messages, etc.)
        if isinstance(event, AIMessageChunk) and isinstance(event.content, str):
            await response.stream_token(event.content)

    await response.send()
