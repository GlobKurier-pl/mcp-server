# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml ./

COPY uv.lock* ./

RUN uv sync --frozen --no-dev

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim

LABEL maintainer="GlobKurier MCP"
LABEL description="MCP Server for GlobKurier API - Hexagonal Architecture"
LABEL version="0.2.0"

RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -m -s /sbin/nologin appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY --chown=appuser:appuser globkurier_mcp /app/globkurier_mcp

RUN mkdir -p /var/log/globkurier-mcp && \
    chown -R appuser:appuser /var/log/globkurier-mcp

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FILE_PATH=/var/log/globkurier-mcp/app.log

USER appuser

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 9000)); s.close()" || exit 1

CMD ["python", "-m", "globkurier_mcp.main"]