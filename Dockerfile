FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy workspace root config
COPY pyproject.toml uv.lock ./

# Copy required packages
COPY core/ core/
COPY mcp-server/ mcp-server/

# Install dependencies (frozen lockfile, no dev deps)
RUN uv sync --directory mcp-server --frozen --no-dev

# Runtime configuration
ENV FORGE_BACKEND=supabase \
    MCP_TRANSPORT=sse \
    PORT=8000

EXPOSE 8000

CMD ["uv", "run", "--directory", "mcp-server", "python", "-m", "forge_mcp.server"]
