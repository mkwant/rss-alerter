FROM python@sha256:6a27522252aef8432841f224d9baaa6e9fce07b07584154fa0b9a96603af7456

COPY --from=ghcr.io/astral-sh/uv@sha256:87a04222b228501907f487b338ca6fc1514a93369bfce6930eb06c8d576e58a4 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Amsterdam
ENV PIP_ROOT_USER_ACTION=ignore
ENV TERM=xterm-256color

RUN apt-get update && apt-get install -y build-essential libffi-dev libssl-dev

# Set the working directory
WORKDIR /app

# Copy metadata for dependency installation
COPY pyproject.toml uv.lock* ./

# Install dependencies inside container Python environment (portable across architectures)
RUN uv sync --no-dev --frozen --no-install-project

# Copy source code
COPY src/rss_alert ./rss_alert

# Runtime folder
RUN mkdir -p history

# Run the main module directly
ENTRYPOINT ["python", "-m", "rss_alert.main"]