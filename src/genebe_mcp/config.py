"""Runtime configuration, read from ``GENEBE_*`` environment variables."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GENEBE_", env_file=".env", extra="ignore")

    # GeneBe backend
    api_url: str = "https://api.genebe.net/cloud/api-public"
    api_key: SecretStr | None = None
    timeout_seconds: float = 30.0

    # HTTP server
    host: str = "0.0.0.0"
    port: int = 17843
    # Proxies whose X-Forwarded-For we believe (uvicorn); nginx on the same host by default.
    trusted_proxies: str = "127.0.0.1,::1"
    mcp_path: str = "/v1/mcp"
    # DNS-rebinding guard: accepted Host / Origin headers (JSON list in the environment variable).
    allowed_hosts: list[str] = ["mcp.genebe.net", "localhost:*", "127.0.0.1:*", "[::1]:*"]
    allowed_origins: list[str] = ["https://mcp.genebe.net", "http://localhost:*", "http://127.0.0.1:*"]

    # Response shaping: keep one tool call within roughly 1-3k tokens.
    max_consequences: int = 8
    max_transcripts: int = 25
    max_text_chars: int = 6000
