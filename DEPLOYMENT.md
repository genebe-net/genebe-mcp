# Wdrożenie produkcyjne

Publiczny endpoint: **https://mcp.genebe.net/v1/mcp** (health: https://mcp.genebe.net/health).

## Gdzie działa

Produkcyjny serwer GeneBe (SSH: `<prod-host>`) (ten sam co api.genebe.net i webapp), obok pozostałych mikroserwisów w `~/docker`.

```
klient MCP ──https──> nginx (mcp.genebe.net, :443)
                       └─> 127.0.0.1:17843  kontener `genebe-mcp` (quay.io/genebeam/genebe-mcp)
                              └─> 127.0.0.1:7180/cloud/api-public  webapp GeneBe (ten sam host)
```

| Element | Szczegóły |
|---|---|
| Skrypt startowy | `~/docker/startMcp.sh` – pobiera `:latest`, zatrzymuje i uruchamia kontener `genebe-mcp` (`--net=host`, `--restart=always`, 512 MB) |
| Port | `GENEBE_PORT=17843`, nasłuch tylko na `127.0.0.1` (`GENEBE_HOST`), niedostępny z zewnątrz |
| Backend | lokalny webapp: `GENEBE_API_URL=http://127.0.0.1:7180/cloud/api-public` (nie api.genebe.net); `GENEBE_API_KEY` nie ustawiony |
| nginx | `/etc/nginx/sites-available/mcp.genebe.net` (symlink w `sites-enabled`); limit 10 req/s na IP (burst 30), bez buforowania (streaming) |
| Certyfikat | Let's Encrypt, wspólny z innymi domenami: `/etc/letsencrypt/live/genebe.net/`, odnawia certbot. Dodanie domeny: `sudo certbot --nginx --expand -d <wszystkie dotychczasowe> -d <nowa> --cert-name genebe.net` |
| Dozwolone hosty | `GENEBE_ALLOWED_HOSTS` (domyślnie `mcp.genebe.net` + localhost); nginx przekazuje oryginalny `Host` |
| Logi | `docker logs genebe-mcp`; nginx: `/var/log/nginx/{access,error}-mcp-genebe-net.log` |

## Adres IP użytkownika (limity backendu)

Backend liczy zapytania anonimowych użytkowników **per IP**, więc serwer MCP przekazuje mu adres prawdziwego użytkownika
w `X-Forwarded-For`:

1. nginx **nadpisuje** `X-Forwarded-For` adresem, który sam widzi (`$remote_addr`), a nie dopisuje do nagłówka klienta.
   Dzięki temu klient nie może podstawić cudzego adresu.
2. uvicorn ufa nagłówkowi tylko od proxy z `GENEBE_TRUSTED_PROXIES` (domyślnie `127.0.0.1,::1`, czyli nginx na tym hoście).
3. `GeneBeClient` dodaje ten adres do każdego wywołania backendu.
4. Tomcat (`server.tomcat.remoteip`) uznaje `X-Forwarded-For` tylko od zaufanych proxy, w tym `127.0.0.1`.

Dlatego `GENEBE_API_URL` musi wskazywać na `http://127.0.0.1:7180/...`. Wywołanie przez publiczne `api.genebe.net`
nie przekaże IP: tamtejszy nginx dopisze publiczny adres tego serwera i backend uzna go za klienta.
Po ustawieniu `GENEBE_API_KEY` limity liczone są na konto, a nie na IP.

## Nowe wydanie

```bash
./dockerize.sh                                  # lokalnie: testy, build, push na quay.io
ssh <prod-host> '~/docker/startMcp.sh' # na serwerze: pull + restart kontenera
curl https://mcp.genebe.net/health              # sprawdzenie
```

Zmiana portu: `GENEBE_PORT` w `~/docker/startMcp.sh` oraz `proxy_pass` w pliku nginx, potem `sudo nginx -t && sudo systemctl reload nginx`.
