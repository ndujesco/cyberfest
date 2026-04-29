import asyncio
from core.http_client import DualClient

_WELL_KNOWN = [
    "/.well-known/openid-configuration",
    "/.well-known/oauth-authorization-server",
    "/oauth/.well-known/openid-configuration",
    "/auth/.well-known/openid-configuration",
    "/oauth/v2/.well-known/openid-configuration",
    "/.well-known/jwks.json",
]

_COMMON_AUTH = [
    "/oauth/authorize", "/oauth2/authorize", "/auth/authorize",
    "/connect/authorize", "/oauth/token", "/oauth2/token",
    "/auth/token", "/connect/token",
]


class OAuthDiscovery:
    def __init__(self, client: DualClient):
        self.client = client

    async def probe(self) -> dict | None:
        for path in _WELL_KNOWN:
            try:
                resp = await self.client.get_anon(path)
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        pass
            except Exception:
                continue
        return None

    async def find_auth_endpoints(self) -> dict[str, int]:
        sem = asyncio.Semaphore(5)
        found: dict[str, int] = {}

        async def _check(path: str):
            async with sem:
                try:
                    resp = await self.client.get_anon(path)
                    if resp.status_code not in (404, 410):
                        found[path] = resp.status_code
                except Exception:
                    pass

        await asyncio.gather(*[_check(p) for p in _COMMON_AUTH])
        return found
