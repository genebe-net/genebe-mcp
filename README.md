# GeneBe MCP

Read-only remote [MCP](https://modelcontextprotocol.io) server that gives AI assistants access to
[GeneBe](https://genebe.net) variant annotation and ACMG classification. Ask *"what is chr6-160585140-T-G?"* or
*"is NM_005577.4:c.4195A>C benign?"* and the assistant answers from GeneBe data — verdict, points, criteria,
gnomAD frequencies, predictor scores, ClinVar — instead of guessing.

> **Research use only.** Not a diagnosis. Results must be reviewed by a qualified specialist.

- Remote only (Streamable HTTP, stateless), no account needed.
- Read-only: no tool changes anything in a GeneBe account.
- Single variants only; no patient data or VCF files.
- Endpoint: `https://mcp.genebe.net/v1/mcp`

## Connect

Claude Code:

```bash
claude mcp add --transport http genebe https://mcp.genebe.net/v1/mcp
```

Cursor / VS Code / other clients that take a JSON config:

```json
{ "mcpServers": { "genebe": { "url": "https://mcp.genebe.net/v1/mcp" } } }
```

## Tools

| Tool | Purpose |
|---|---|
| `annotate_variant` | Main tool. Any notation (coordinates, HGVS, rsID, SPDI) → ACMG verdict, frequencies, scores, ClinVar, consequences, GeneBe links |
| `explain_acmg_decision_path` | Why each classification criterion applied, as text |
| `convert_variant` | HGVS / rsID / SPDI → hg38 coordinates |
| `get_variant_effects` | Per-transcript consequences (HGVS c./p., impact) |
| `get_gene` | Gene identifiers, location, MANE Select, ClinGen gene–disease validity, transcripts |
| `liftover_coordinate` | Positions, intervals or variants between hg19 / hg38 / t2t |

Default genome is hg38. Every tool returns text plus `structuredContent` that follows the tool's `outputSchema`.
Large lists are capped and flagged with `truncated`, so a call stays within roughly 1–3k tokens.

`annotate_variant` has a `summary` field reserved for the human-readable variant description. The MCP server never
writes this text itself; it is passed through once the GeneBe backend returns it, so the website, REST API and MCP
always say the same thing. Until then it is `null`.

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
| `GENEBE_TRUSTED_PROXIES` | `127.0.0.1,::1` | Proxy, którym wierzymy w `X-Forwarded-For` (adres użytkownika przekazywany do backendu, patrz DEPLOYMENT.md) |
| `GENEBE_MAX_CONSEQUENCES`, `GENEBE_MAX_TRANSCRIPTS`, `GENEBE_MAX_TEXT_CHARS` | `8`, `25`, `6000` | Response size limits |

Docker: `docker build -t genebe-mcp . && docker run -p 17843:17843 genebe-mcp`.
Rate limiting per client IP is expected at the reverse proxy.
Production deployment (host, nginx, release steps): see [DEPLOYMENT.md](DEPLOYMENT.md).

## Publishing to the MCP Registry

`server.json` describes the server for the [Official MCP Registry](https://registry.modelcontextprotocol.io).
A test keeps its version and description in sync with `pyproject.toml` and the server code.

1. Prove ownership of `genebe.net` (DNS TXT record) for the `net.genebe/*` namespace:
   `mcp-publisher login dns --domain genebe.net --private-key <key>`
2. Bump the version in `pyproject.toml` **and** `server.json`, then `mcp-publisher publish`.

## Data and attribution

Results combine data from GeneBe, gnomAD, ClinVar, UniProt, ClinGen and dbNSFP predictors; check each source's
license terms before redistributing. The server stores nothing and logs no variant input.
