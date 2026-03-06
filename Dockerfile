FROM python@sha256:6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456

COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color

# Set the working directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock* ./
RUN uv sync \
    --no-dev \
    --frozen \
    --no-install-project \
    --system

# Copy source
COPY src/rss_alert ./rss_alert

# Runtime folder
RUN mkdir -p history

ENTRYPOINT ["python", "-m", "rss_alert.main"]
# ENTRYPOINT ["/bin/bash"]