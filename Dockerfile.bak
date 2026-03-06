# Base Python image
FROM python:3.14-slim

# Copy uv binary from upstream image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Copy metadata for dependency installation
COPY pyproject.toml uv.lock* ./

# Pre-install all dependencies in container Python
RUN uv sync --no-dev --frozen

# Copy source code
COPY src/rss_alert ./rss_alert

# Runtime folder
RUN mkdir -p history

ENTRYPOINT ["uv", "run", "rss_alert/main.py"]