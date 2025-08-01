FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV HF_HUB_DISABLE_TELEMETRY=1
ENV HF_HOME=/tmp/huggingface_cache

ARG RERANK_ENABLED=false

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

ENV PATH="/app/.venv/bin:${PATH}"

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
    if [ "$RERANK_ENABLED" = "true" ]; then \
        echo "Installing with rerank dependencies..." && \
        uv sync --frozen --no-install-project --group rerank; \
    else \
        uv sync --frozen --no-install-project; \
    fi

ENV PYTHONPATH=/app

COPY . /app

# sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$RERANK_ENABLED" = "true" ]; then \
        uv sync --group rerank; \
    else \
        uv sync; \
    fi

EXPOSE 8444

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8444"]
