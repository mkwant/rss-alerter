FROM python:3.14

COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color

WORKDIR /app

# Copy files
COPY pyproject.toml uv.lock* src/ ./src/

# Install dependencies only
RUN uv sync --no-dev --frozen --no-install-project

# Install project itself (creates module + CLI)
RUN uv pip install .

# Runtime folder
RUN mkdir -p /app/history

# Use Python module for now (CLI can be used once installed)
ENTRYPOINT ["python", "-m", "rss_alert.main"]