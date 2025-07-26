FROM python:3.12-slim

WORKDIR /mcp_server

ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -y --no-install-recommends \
    gcc \
    libc-dev \
    libpq-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# install uv
# see: https://docs.astral.sh/uv/guides/integration/docker/
COPY --from=ghcr.io/astral-sh/uv:0.7.10 /uv /uvx /bin/

ENV PATH="/mcp_server/.venv/bin:${PATH}"

# compiling Python source files to bytecode to improve startup time
# see: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv cache
# see: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# install deps
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/mcp_server

COPY . /mcp_server

# sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

CMD ["mcp", "run", "app/main.py:mcp", "--transport", "streamable-http"]
