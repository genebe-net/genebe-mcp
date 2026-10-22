"""Thin async client for the GeneBe public REST API.

Returns raw JSON; shaping it for models is the job of :mod:`genebe_mcp.mappers`.
"""

from typing import Any
from urllib.parse import quote

import httpx

from genebe_mcp import __version__
from genebe_mcp.caller import client_ip
from genebe_mcp.config import Settings
from genebe_mcp.errors import GeneBeError

type Json = Any


class GeneBeClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        headers = {"User-Agent": f"genebe-mcp/{__version__}", "Accept": "application/json"}
        if settings.api_key is not None:
            headers["Authorization"] = f"Bearer {settings.api_key.get_secret_value()}"
        self._http = httpx.AsyncClient(
            base_url=settings.api_url.rstrip("/") + "/",
            headers=headers,
            timeout=settings.timeout_seconds,
            transport=transport,
            event_hooks={"request": [_forward_client_ip]},
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def annotate(self, variant: str, genome: str, transcript: str | None, gene_symbol: str | None) -> Json:
        params = {
            "variant": variant,
            "genome": genome.upper(),
            "transcript": transcript,
            "gene_symbol": gene_symbol,
        }
        return await self._request("GET", "v1/variant-relaxed", params=params)

    async def convert(self, ids: list[str], input_genome: str) -> Json:
        params = {"inputGenome": input_genome.upper(), "ignoreErrors": "true"}
        return await self._request("POST", "v1/convert", params=params, json=ids)

    async def effects(self, chr_: str, pos: int, ref: str, alt: str) -> Json:
        body = [{"chr": chr_, "pos": pos, "ref": ref, "alt": alt, "genome": "hg38"}]
        return await self._request("POST", "v1/effect", json=body)

    async def gene(self, identifier: str) -> Json:
        return await self._request("GET", f"v1/genes/{_path_segment(identifier)}")

    async def transcripts(self, identifier: str) -> Json:
        return await self._request("GET", f"v1/genes/{_path_segment(identifier)}/transcripts")

    async def liftover(self, queries: list[str], from_genome: str, to_genome: str) -> Json:
        params = {"from": from_genome, "dest": to_genome}
        return await self._request("POST", "v2/liftover", params=params, json=queries)

    async def decision_path_text(self, chr_: str, pos: int, ref: str, alt: str, tree: str, version: str) -> str:
        params = {"chr": chr_, "pos": pos, "ref": ref, "alt": alt, "tree": tree, "version": version}
        response = await self._send(
            "GET",
            "v1/acmg/classifications/decision-path/text",
            params=params,
            headers={"Accept": "text/plain"},
        )
        return response.text

    async def _request(self, method: str, path: str, **kwargs: Any) -> Json:
        return (await self._send(method, path, **kwargs)).json()

    async def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        if "params" in kwargs:
            kwargs["params"] = {k: v for k, v in kwargs["params"].items() if v is not None}
        try:
            response = await self._http.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise GeneBeError("GeneBe did not respond in time. Try again in a moment.") from exc
        except httpx.HTTPError as exc:
            raise GeneBeError("Could not reach the GeneBe API. Try again in a moment.") from exc
        if response.is_success:
            return response
        raise _error_for(response)


async def _forward_client_ip(request: httpx.Request) -> None:
    """Tell the backend which end user this call is on behalf of (it rate-limits anonymous users per IP)."""
    if (ip := client_ip.get()) is not None:
        request.headers["X-Forwarded-For"] = ip


def _path_segment(value: str) -> str:
    return quote(value.strip(), safe=":")


def _error_for(response: httpx.Response) -> GeneBeError:
    status = response.status_code
    if status == 404:
        return GeneBeError("GeneBe has no record for this identifier. Check the spelling or try another identifier.")
    if status == 429:
        return GeneBeError("GeneBe rate limit reached. Wait a little and try again.")
    if status in (400, 422):
        return GeneBeError(
            "GeneBe could not interpret the request. For variants use 'chr-pos-ref-alt' "
            "(e.g. '6-160585140-T-G'), HGVS with a transcript (e.g. 'NM_005577.4:c.4195A>C'), "
            "an rsID or SPDI, and make sure the genome (hg19/hg38) matches the coordinates."
        )
    return GeneBeError("GeneBe is temporarily unavailable. Try again later.")
