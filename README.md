# SEAS

<p align="center">
  <a href="https://yarnpkg.com/">
    <img alt="SEAS-logo" src="ui/public/images/seas-logo.svg" width="256"/>
  </a>
</p>

<p align="center">
  SEAS - A Smart Enrollment Advisory System for CTU
</p>

---

## Prerequisites

- Git
- Docker and Docker Compose
- For UI: Node.js 20+ and Yarn (Berry v4)
- For API: `uv` (Python package and project manager)

## Setup

Get started by cloning this repository:

```bash
git clone https://github.com/minhnguyent546/seas.git
cd seas
```

### Development setup

#### Development setup for the UI

The UI is developed with React, TypeScript, and Vite as the build tool. It uses Yarn as the package manager.

- Install dependencies:

```bash
cd ui
yarn
```

- Create a `.env` file in `ui/` with the following content:

```
VITE_API_URL=<YOUR_API_URL>
VITE_REPORT_ISSUE_LINK=<LINK_TO_SOME_GITHUB_ISSUE>
```

- Start development:

```bash
yarn dev --port=5333 --host=0.0.0.0
```

Point your browser to `http://localhost:5333` to see the chat UI.

#### Development setup for the API

The API is built with FastAPI, SQLAlchemy, and LangChain. The recommended way to set up the API is via Docker Compose.

The repository contains multiple Compose files:

- `docker-compose.yaml`: base services (Postgres, Qdrant, Adminer, API)
- `docker-compose.dev.yaml`: development overrides (local builds, hot reload, extra services)
- `docker-compose.cuda.yaml`: production GPU overrides
- `docker-compose.dev-cuda.yaml`: development GPU overrides

First, create a `.env` file in the project root with the following content:

```
# project name
PROJECT_NAME="SEAS - Smart Enrollment Advisory System"

# environment
ENVIRONMENT=development  # development, production

# frontend
FRONTEND_HOST=http://localhost:5333

# backend
API_PREFIX=/api/v1
API_PORT=8444
BACKEND_CORS_ORIGINS='http://localhost:5333'

# google oauth2
GOOGLE_OAUTH2_CLIENT_ID=YOUR_GOOGLE_OAUTH2_CLIENT_ID
GOOGLE_OAUTH2_CLIENT_SECRET=YOUR_GOOGLE_OAUTH2_CLIENT_SECRET

# github oauth2
GITHUB_OAUTH2_CLIENT_ID=YOUR_GITHUB_OAUTH2_CLIENT_ID
GITHUB_OAUTH2_CLIENT_SECRET=YOUR_GITHUB_OAUTH2_CLIENT_SECRET

# jwt
SECRET_KEY=YOUR_SECRET_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30 # 30 minutes

# postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=seas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ENTER_YOUR_PREFERRED_PASSWORD
FIRST_USER_USERNAME=root
FIRST_USER_PASSWORD=ENTER_YOUR_PREFERRED_PASSWORD

# email
SMTP_TLS=true
SMTP_SSL=false
SMTP_HOST=ENTER_SMTP_HOST_HERE
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=noreply@example.com

# llm
CHAT_MODEL="google/gemini-2.5-flash"
TABLE_SUMMARY_MODEL="openai/gpt-4o"
GOOGLE_API_KEY=""
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
OPENROUTER_API_KEY=  # use openrouter/ prefix to use OpenRouter as provider, e.g., openrouter/google/gemini-2.5-flash

# embeddings model
BAAI_EMBEDDING_MODEL="BAAI/bge-m3"
CHUNK_SIZE=2048
CHUNK_OVERLAP=256

QUERY_EXPANSION_MODEL="openrouter/google/gemini-2.5-flash"

# reranking model
BAAI_RERANKER_MODEL="BAAI/bge-reranker-v2-m3"

# qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=ENTER_YOUR_QDRANT_API_KEY
QDRANT_COLLECTION_NAME=embeddings_bge-m3_1024
QDRANT_VECTOR_SIZE=1024  # embeddings dimension

# preload models on startup
PRELOAD_HF_MODELS=true

# config for adding document in batch
BATCH_DOCUMENT_UPLOAD_MAX_BATCH_SIZE=20
BATCH_DOCUMENT_UPLOAD_MAX_TOTAL_CHUNKS=5_000

# Docker images
API_IMAGE=seas-api
API_TAG=latest
```

Update passwords with your preferences and API keys.

Build and run the stack with live reload for the API:

```bash
# Development with CPU (default)
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml up --build --watch

# Development with GPU (requires NVIDIA runtime and drivers)
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml -f docker-compose.dev-cuda.yaml up --build

# Use external databases (external Postgres and Qdrant)
# Update the following variables in .env file to point to the remote host
# - POSTGRES_HOST
# - POSTGRES_PORT
# - QDRANT_HOST
# - QDRANT_PORT
# and then run:
docker compose -f docker-compose.yaml -f docker-compose.dev.yaml -f docker-compose.dev-cuda.yaml -f docker-compose.external-dbs.yaml up --build --watch

```

Services:

- FastAPI backend: http://localhost:8444/docs
- Postgres: localhost:5433
- Qdrant: http://localhost:6333/dashboard
- Adminer: http://localhost:8555
- Maildev: http://localhost:1080

### Production setup

The base compose expects an existing API image (`API_IMAGE` and optional `API_TAG`). Build and supply one:

```bash
# Build API image
cd api
docker build -t your-registry/seas-api:latest .
# (Optional) push to registry
# docker push your-registry/seas-api:latest

# From repo root, run with the image
cd ..
API_IMAGE=your-registry/seas-api API_TAG=latest ENVIRONMENT=production \
docker compose -f docker-compose.yaml up -d --build
```

For GPU-enabled production (CUDA 12.6):

```bash
API_IMAGE=your-registry/seas-api API_TAG=latest ENVIRONMENT=production \
docker compose -f docker-compose.yaml -f docker-compose.cuda.yaml up -d --build
```

The provided Compose files do not include the UI container by default. Deploy the UI separately. Here is an example of using `serve` for deploying static files from `ui/`:

```bash
cd ui
yarn build
yarn dlx serve -s dist -l 0.0.0.0:5333
```
