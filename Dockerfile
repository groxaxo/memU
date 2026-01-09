# Multi-stage Dockerfile for MemU MCP Server
# Supports stdio transport for MCP clients like Claude Desktop

# ============================================================================
# Stage 1: Builder - Install dependencies and build Rust components
# ============================================================================
FROM python:3.13-slim-bookworm AS builder

# Install system dependencies including Rust for maturin build
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /build

# Copy dependency files
COPY pyproject.toml Cargo.toml Cargo.lock ./
COPY setup.cfg MANIFEST.in ./

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy source code
COPY src ./src
COPY tests ./tests

# Build the package with dependencies
RUN uv pip install --system -e .

# Install MCP server dependency
RUN uv pip install --system mcp

# ============================================================================
# Stage 2: Runtime - Minimal image for running the server
# ============================================================================
FROM python:3.13-slim-bookworm

# Create non-root user for security
RUN useradd -m -u 1000 memu && \
    mkdir -p /app /data && \
    chown -R memu:memu /app /data

WORKDIR /app

# Copy built packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY --chown=memu:memu src ./src
COPY --chown=memu:memu pyproject.toml setup.cfg MANIFEST.in ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEMU_DATA_DIR=/data \
    PATH="/app:${PATH}"

# Switch to non-root user
USER memu

# Health check (for debugging - not used in stdio mode)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Volume for persistent data
VOLUME ["/data"]

# Entrypoint runs the MCP server in stdio mode
# MCP clients communicate via stdin/stdout
ENTRYPOINT ["python", "-m", "memu.mcp_server"]
