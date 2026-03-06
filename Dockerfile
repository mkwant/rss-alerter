FROM python@sha256:5e2dbd4bbdd9c0e67412aea9463906f74a22c60f89eb7b5bbb7d45b66a2b68a6 AS base

# Install UV
COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

# Set timezone
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Install system dependencies (for SSL, building wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml
COPY pyproject.toml /app/

# Install dependencies via uv
RUN uv sync

# Copy source code
COPY . /app

# Make history folder writable
RUN mkdir -p /app/history

# Environment variables for Telegram (can be overridden at runtime)
#ENV TELEGRAM_TOKEN=""
#ENV TELEGRAM_CHAT_ID=""

# Default entrypoint: run CLI via uv
ENTRYPOINT ["uv", "run", "-m", "rss_alert.main"]