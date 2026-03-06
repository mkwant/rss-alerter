FROM python@sha256:6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456 AS base

# Install UV
COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

# Set env vars
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM xterm-256color

WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml /app/

# Copy source code
COPY . /app

# Make history folder writable
RUN mkdir -p /app/history

# Install dependencies via uv
RUN uv sync --no-dev --frozen

ENTRYPOINT ["rss-alert"]