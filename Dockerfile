FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS=true

RUN apt-get update && apt-get install -y 

RUN apt-get update && apt-get install -y chromium chromium-driver && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./ 

RUN uv sync --frozen

COPY src/ ./src/
COPY cli/ ./cli/
COPY mcp/ ./mcp/

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && mkdir -p /app/data/linkedin_profiles \
    && chown -R app:app /app/data

USER app

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    HOST=0.0.0.0 \
    PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["uv", "run", "linkedin_mcp", "sse"]
