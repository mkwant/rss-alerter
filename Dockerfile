FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . .

RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["rss-alert"]