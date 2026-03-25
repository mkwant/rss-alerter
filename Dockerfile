FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

# Omit development dependencies
ENV UV_NO_DEV=1

# Copy project metadata to leverage layer caching for dependencies
COPY pyproject.toml uv.lock ./

# Use cache mount to speed up dependency installs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

# Copy rest of the source code
COPY . .

# Install the project itself
RUN uv pip install .

# Set PATH to find the installed cli tool
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["rss-alert"]