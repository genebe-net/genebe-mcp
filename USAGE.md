# Using GeneBe MCP

GeneBe MCP is a read-only [MCP](https://modelcontextprotocol.io) server for variant annotation and ACMG classification
by [GeneBe](https://genebe.net). It is hosted for you; no account or API key is needed.

> **Research use only.** Not a diagnosis. Results must be reviewed by a qualified specialist.

- Endpoint (Streamable HTTP): `https://mcp.genebe.net/v1/mcp`
- Health check: `https://mcp.genebe.net/health`
- Requests are rate limited per client IP.

## Connect

**Claude Code**

```bash
claude mcp add --transport http genebe https://mcp.genebe.net/v1/mcp
```

**Cursor, VS Code and other clients with a JSON config**

```json
{ "mcpServers": { "genebe": { "url": "https://mcp.genebe.net/v1/mcp" } } }
```

**MCP Inspector** (tool list, schemas, raw responses)

```bash
npx @modelcontextprotocol/inspector
```

Choose the Streamable HTTP transport and enter the endpoint URL.

## Try it

Ask your assistant:

- "What is chr6-160585140-T-G?"
- "Is NM_005577.4:c.4195A>C benign?"
- "Why is this variant classified as it is?" (explains the ACMG decision path)
- "Give me the MANE Select transcript and ClinGen validity for TP53."

Or call a tool directly:

```bash
curl -s -X POST https://mcp.genebe.net/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"annotate_variant","arguments":{"variant":"chr6-160585140-T-G"}}}'
```

See the tool list in the [README](README.md#tools). Variants can be given as coordinates, HGVS, rsID or SPDI; the
default genome build is hg38.

## Run your own copy

```bash
# from source (Python 3.13, uv)
uv sync
GENEBE_PORT=8765 uv run python -m genebe_mcp          # http://localhost:8765/v1/mcp

# Docker
docker build -t genebe-mcp .
docker run --rm -p 17843:17843 genebe-mcp             # http://localhost:17843/v1/mcp
```

Configuration is by `GENEBE_*` environment variables, see the table in the [README](README.md#develop).

## Tests

```bash
uv run pytest             # unit tests, no network
uv run pytest -m live     # smoke tests against the real GeneBe API
uv run ruff check . && uv run ruff format --check . && uv run mypy
```
