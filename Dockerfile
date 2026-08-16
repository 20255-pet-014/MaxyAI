# ==============================================================================
# Maxy Autonomous Multi-Agent Research & Publishing Platform - Dockerfile
# ==============================================================================

FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Astral UV for ultra-fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1 \
    PORT=8501

# Copy dependency definitions
COPY mcp_server/pyproject.toml /app/mcp_server/pyproject.toml
COPY mcp_client/pyproject.toml /app/mcp_client/pyproject.toml

# Install dependencies for both server and client using uv
RUN cd /app/mcp_server && uv pip install --system -e . && \
    uv pip install --system fastapi uvicorn sse-starlette markdown

# Copy project source code
COPY mcp_server /app/mcp_server
COPY mcp_client /app/mcp_client
COPY web /app/web
COPY docs /app/docs
COPY data /app/data
COPY README.md /app/README.md

# Expose web dashboard port
EXPOSE 8501

# Default command: Start Maxy Web Dashboard & FastMCP API
CMD ["python", "-m", "uvicorn", "web.server:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8501"]
