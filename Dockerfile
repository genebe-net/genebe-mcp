FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md .python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim
RUN useradd --system --uid 10001 app
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 17843
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('GENEBE_PORT', '17843'), timeout=2)"
CMD ["python", "-m", "genebe_mcp"]
