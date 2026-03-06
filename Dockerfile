FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --frozen --group mcp

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

ENTRYPOINT ["uv", "run", "linkedin-spider-mcp", "serve", "--transport", "stdio"]
