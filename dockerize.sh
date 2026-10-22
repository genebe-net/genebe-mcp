#!/usr/bin/env bash
# Builds the image and pushes it to quay.io as :<version> and :latest.
# The version is taken from pyproject.toml. Run `docker login quay.io` first.
set -euo pipefail
cd "$(dirname "$0")"

NAME=quay.io/genebeam/genebe-mcp
VERSION=$(uv run --no-sync python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')

uv run ruff check .
uv run mypy
uv run pytest -q

docker build -t "$NAME:$VERSION" -t "$NAME:latest" .
docker push "$NAME:$VERSION"
docker push "$NAME:latest"
