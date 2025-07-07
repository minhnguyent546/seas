#!/usr/bin/env bash

# run pytest locally

set -e

export POSTGRES_DB=seas-test
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD="$(openssl rand -hex 16)"
export FIRST_USER_USERNAME=root
export FIRST_USER_PASSWORD="$(openssl rand -hex 16)"
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5789
export POSTGRES_IMAGE='postgres:17.5-bookworm'

# stop the container on error or exit
trap 'echo "Stopping postgres container"; docker stop $(docker ps -q --filter ancestor="$POSTGRES_IMAGE")' EXIT

docker run -d --rm \
  -e POSTGRES_DB="$POSTGRES_DB" \
  -e POSTGRES_USER="$POSTGRES_USER" \
  -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  -p "${POSTGRES_PORT}:5432" \
  "$POSTGRES_IMAGE"

# wait for the database to be ready
until docker exec $(docker ps -q --filter ancestor="$POSTGRES_IMAGE") pg_isready -U postgres; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

uv run pytest --cov=app --cov-report=html --capture=no
