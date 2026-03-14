FROM python:3.11-slim

WORKDIR /app

# System deps for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml langgraph.json .env* ./
COPY src/ src/

# Install the project and langgraph CLI with in-memory runtime
# (no Postgres/Redis needed -- the inmem runtime handles persistence)
RUN pip install --no-cache-dir -e "." "langgraph-cli[inmem]>=0.4.0"

# langgraph dev serves on port 2024
EXPOSE 2024

# --no-reload: disable file watcher (no source changes in container)
# --no-browser: don't try to open a browser
# --host 0.0.0.0: accept connections from outside the container
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-reload", "--no-browser"]
