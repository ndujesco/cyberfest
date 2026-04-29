import asyncio
from typing import Optional

import httpx

_UA = "Mozilla/5.0 (compatible; SpecterAPI/0.1; security-research)"

_DEFAULT_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json, text/html, */*",
}


class DualClient:
    """Two independent httpx sessions — User A (victim) and User B (attacker)."""

    def __init__(
        self,
        target: str,
        user_a_token: Optional[str] = None,
        user_b_token: Optional[str] = None,
        proxy: Optional[str] = None,
        delay: float = 0.0,
        timeout: float = 12.0,
        verify: bool = True,
    ):
        self.target = target.rstrip("/")
        self.user_a_token = user_a_token
        self.user_b_token = user_b_token
        self.delay = delay

        proxies = {"http://": proxy, "https://": proxy} if proxy else None

        def _make_client(token: Optional[str]) -> httpx.AsyncClient:
            headers = dict(_DEFAULT_HEADERS)
            if token:
                headers["Authorization"] = f"Bearer {token}"
            return httpx.AsyncClient(
                headers=headers,
                proxies=proxies,
                timeout=timeout,
                verify=verify,
                follow_redirects=True,
            )

        self._anon = _make_client(None)
        self._a = _make_client(user_a_token)
        self._b = _make_client(user_b_token)

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return self.target + ("" if path.startswith("/") else "/") + path

    async def _wait(self):
        if self.delay > 0:
            await asyncio.sleep(self.delay)

    async def get_anon(self, path: str, **kw) -> httpx.Response:
        await self._wait()
        return await self._anon.get(self._url(path), **kw)

    async def get_a(self, path: str, **kw) -> httpx.Response:
        await self._wait()
        return await self._a.get(self._url(path), **kw)

    async def get_b(self, path: str, **kw) -> httpx.Response:
        await self._wait()
        return await self._b.get(self._url(path), **kw)

    async def request_a(self, method: str, path: str, **kw) -> httpx.Response:
        await self._wait()
        return await self._a.request(method, self._url(path), **kw)

    async def request_b(self, method: str, path: str, **kw) -> httpx.Response:
        await self._wait()
        return await self._b.request(method, self._url(path), **kw)

    async def aclose(self):
        await self._anon.aclose()
        await self._a.aclose()
        await self._b.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()
