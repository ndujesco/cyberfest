import asyncio

from core.http_client import DualClient
from core.session import Session
from core.finding import Finding, Severity

_NO_AUTH_OK = {200, 201, 204}
_CRITICAL_KW = {"admin", "debug", "config", "internal", "manage", "secret"}
_HIGH_KW = {"export", "dump", "download", "backup", "user", "account", "profile", "password", "token"}


class Prober:
    def __init__(self, client: DualClient, session: Session):
        self.client = client
        self.session = session

    async def probe_all(self, candidates: list[dict]) -> list[Finding]:
        sem = asyncio.Semaphore(10)

        async def _one(c):
            async with sem:
                try:
                    return await self._probe(c)
                except Exception:
                    return None

        results = await asyncio.gather(*[_one(c) for c in candidates])
        return [r for r in results if r]

    async def _probe(self, c: dict) -> Finding | None:
        path = c["path"]
        method = c.get("method", "GET")
        source = c.get("source", "")

        try:
            resp = await self.client.get_anon(path)
        except Exception:
            return None

        status = resp.status_code
        size = len(resp.content)
        ct = resp.headers.get("content-type", "")
        auth_required = status not in _NO_AUTH_OK

        self.session.add_endpoint(
            path=path, method=method, status_code=status,
            auth_required=auth_required, response_size=size,
            source_file=source, content_type=ct,
        )

        if status in _NO_AUTH_OK:
            sev = self._classify(path, size)
            return Finding(
                module="ghost",
                severity=sev,
                title=f"Unauthenticated endpoint — {method} {path}",
                endpoint=f"{method} {path}",
                evidence=(
                    f"HTTP {status} with no Authorization header. "
                    f"Response: {size:,} bytes, Content-Type: {ct}"
                ),
                cwe="CWE-306",
            )
        return None

    def _classify(self, path: str, size: int) -> Severity:
        pl = path.lower()
        if any(kw in pl for kw in _CRITICAL_KW):
            return Severity.CRITICAL
        if any(kw in pl for kw in _HIGH_KW) or size > 10_000:
            return Severity.HIGH
        return Severity.MEDIUM
