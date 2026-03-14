FROM python:3.11-slim

WORKDIR /app

# System deps for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml langgraph.json ./
COPY src/ src/

# Install the project and langgraph CLI (inmem mode = dev server, no Postgres/Redis)
RUN pip install --no-cache-dir -e "." "langgraph-cli[inmem]>=0.4.0"

# langgraph dev listens on 2024 by default
EXPOSE 2024

# Run the LangGraph dev server, binding to 0.0.0.0 so Docker can reach it
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"]
