# Development

Notes for people who want to run, change or self-host GeneBe MCP. To simply *use* it, see the [README](README.md).

## Architecture

```
MCP client ──Streamable HTTP──> genebe-mcp (Python, stateless) ──httpx──> api.genebe.net/cloud/api-public (Java)
```

```
src/genebe_mcp/
  server.py     app factory, server instructions, /health
  tools/        one module per tool; thin: resolve input → call client → map
  client.py     async httpx client for the GeneBe REST API, errors written for the model
  resolve.py    any notation → hg38 coordinates (via the backend's /v1/convert)
  mappers.py    pure functions: REST JSON → models (the place to adapt when the REST API changes)
  models.py     Pydantic models = tool output schemas
  truncate.py   response size limits
```

## Develop

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run ruff check . && uv run ruff format --check . && uv run mypy
uv run pytest              # unit tests, no network
uv run pytest -m live      # smoke tests against the real GeneBe API
uv run python -m genebe_mcp   # serves on :17843, endpoint /v1/mcp, health at /health
```

Configuration (environment variables, see `.env.example`):

| Variable | Default | |
|---|---|---|
| `GENEBE_API_URL` | `https://api.genebe.net/cloud/api-public` | Backend base URL |
| `GENEBE_API_KEY` | – | Service key sent as `Authorization: Bearer`; never exposed to MCP clients |
| `GENEBE_PORT` / `GENEBE_HOST` | `17843` / `0.0.0.0` | Listen address |
| `GENEBE_ALLOWED_HOSTS` / `GENEBE_ALLOWED_ORIGINS` | `mcp.genebe.net`, localhost | JSON lists of accepted `Host` / `Origin` headers (DNS-rebinding guard; `host:*` = any port) |
| `GENEBE_TRUSTED_PROXIES` | `127.0.0.1,::1` | Reverse proxies whose `X-Forwarded-For` is trusted; the end user's IP is passed on to the backend for per-IP rate limits |
| `GENEBE_MAX_CONSEQUENCES`, `GENEBE_MAX_TRANSCRIPTS`, `GENEBE_MAX_TEXT_CHARS` | `8`, `25`, `6000` | Response size limits |

Docker: `docker build -t genebe-mcp . && docker run -p 17843:17843 genebe-mcp`.
Rate limiting per client IP is expected at the reverse proxy.
See [USAGE.md](USAGE.md) for connection examples and running locally.


## Data and attribution

Results combine data from GeneBe, gnomAD, ClinVar, UniProt, ClinGen and dbNSFP predictors; check each source's
license terms before redistributing.
