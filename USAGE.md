# Uruchamianie i testowanie

## Wersja produkcyjna (mcp.genebe.net)

Zdeployowany serwer: `https://mcp.genebe.net/v1/mcp` (Streamable HTTP, bez konta i klucza). Szczegóły wdrożenia: [DEPLOYMENT.md](DEPLOYMENT.md).

```bash
# sprawdzenie, czy żyje
curl https://mcp.genebe.net/health

# Claude Code
claude mcp add --transport http genebe https://mcp.genebe.net/v1/mcp

# lista narzędzi surowym JSON-RPC
curl -s -X POST https://mcp.genebe.net/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# wywołanie narzędzia
curl -s -X POST https://mcp.genebe.net/v1/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"annotate_variant","arguments":{"variant":"chr6-160585140-T-G"}}}'
```

Klienci z konfiguracją JSON (Cursor, VS Code itp.): `{ "mcpServers": { "genebe": { "url": "https://mcp.genebe.net/v1/mcp" } } }`.
MCP Inspector (`npx @modelcontextprotocol/inspector`): transport Streamable HTTP, URL jak wyżej.
Obowiązuje limit ok. 10 zapytań/s na adres IP.

## Lokalne uruchomienie

Backend wybiera się zmienną `GENEBE_API_URL`. Domyślnie jest to `https://api.genebe.net/cloud/api-public`.
Zmienne można też wpisać do `.env` (wzór: `.env.example`).

### Uruchomienie serwera

```bash
# backend: api.genebe.net (domyślnie)
GENEBE_PORT=8765 uv run python -m genebe_mcp

# backend: lokalny
GENEBE_API_URL=http://localhost:7180/cloud/api-public GENEBE_PORT=8765 uv run python -m genebe_mcp
```

- Endpoint MCP: `http://localhost:8765/v1/mcp`
- Sprawdzenie: `curl localhost:8765/health`
- Jeśli lokalny backend stosuje limity, dodaj `GENEBE_API_KEY=<klucz>`.

### Wywoływanie narzędzi

**Prawdziwy asystent (Claude Code):**

```bash
claude mcp add --transport http genebe-local http://localhost:8765/v1/mcp
```

Potem można zapytać np. „czym jest 6-160585140-T-G?” albo „czy NM_005577.4:c.4195A>C jest łagodny?”.

**MCP Inspector** (lista narzędzi, schematy, surowe odpowiedzi):

```bash
npx @modelcontextprotocol/inspector
```

Wybierz transport Streamable HTTP i podaj URL serwera.

## Kontener Docker

```bash
docker build -t genebe-mcp .

# backend: api.genebe.net
docker run --rm -p 17843:17843 genebe-mcp

# backend: localhost:7180 na hoście (na Linuksie potrzebny --add-host)
docker run --rm -p 17843:17843 \
  --add-host=host.docker.internal:host-gateway \
  -e GENEBE_API_URL=http://host.docker.internal:7180/cloud/api-public \
  genebe-mcp
```

Endpoint MCP to wtedy `http://localhost:17843/v1/mcp`.

## Testy automatyczne

```bash
uv run pytest                 # jednostkowe, bez sieci (zapisane odpowiedzi w tests/fixtures)
uv run pytest -m live         # smoke testy na prawdziwym API

# smoke testy na lokalnym backendzie
GENEBE_API_URL=http://localhost:7180/cloud/api-public uv run pytest -m live
```

## Kontrola jakości

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy
```

## Publikacja obrazu

```bash
docker login quay.io
./dockerize.sh                # testy, build i push jako :<wersja> oraz :latest
```

Wersja pochodzi z `pyproject.toml`. Przed kolejnym wydaniem podbij ją też w `server.json`.
