FROM python@sha256:6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456

COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487c338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color

WORKDIR /app

# Copy metadata for dependency installation
COPY pyproject.toml uv.lock* ./

# Install dependencies (only)
RUN uv sync --no-dev --frozen --no-install-project

# Copy source directly to /app/rss_alert so module is importable
COPY src/rss_alert ./rss_alert

# Runtime folder
RUN mkdir -p history

# Run main.py
ENTRYPOINT ["python", "-m", "rss_alert.main"]