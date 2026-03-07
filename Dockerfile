FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=0 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS=true

RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    /usr/share/doc/* /usr/share/man/* /usr/share/info/*

RUN useradd --create-home --shell /bin/bash app

WORKDIR /app
RUN chown app:app /app

USER app

COPY --chown=app:app pyproject.toml uv.lock README.md ./
COPY --chown=app:app src/ ./src/

RUN uv sync --frozen --group mcp --no-dev --no-editable

ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    TRANSPORT=stdio

EXPOSE 8080

CMD uv run linkedin-spider-mcp serve --transport $TRANSPORT --host 0.0.0.0 --port 8080
