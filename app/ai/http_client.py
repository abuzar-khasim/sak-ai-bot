import httpx


def create_http_client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=10.0,
        pool=5.0,
    )

    limits = httpx.Limits(
        max_connections=50,
        max_keepalive_connections=20,
        keepalive_expiry=30.0,
    )

    return httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        headers={
            "User-Agent": "SAK-AI/1.0",
        },
    )