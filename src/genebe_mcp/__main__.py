import uvicorn

from genebe_mcp.config import Settings
from genebe_mcp.server import create_app


def main() -> None:
    settings = Settings()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=settings.trusted_proxies,
    )


if __name__ == "__main__":
    main()
