# Base Python image
FROM python:3.14-slim

# Copy uv binary from upstream image (correct SHA)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color
ENV UVX_PATH=/uvx
ENV PATH="${UVX_PATH}/bin:$PATH"
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libffi-dev libssl-dev

# Set working directory
WORKDIR /app

# Copy metadata for dependency installation
COPY pyproject.toml uv.lock* ./

# Pre-install all dependencies into uv environment
RUN uv sync --no-dev --frozen --install-dir ${UVX_PATH}

# Copy source code
COPY src/rss_alert ./rss_alert

# Runtime folder
RUN mkdir -p history

# Entrypoint: uv will use the prepopulated environment
ENTRYPOINT ["uv", "run", "rss_alert/main.py"]