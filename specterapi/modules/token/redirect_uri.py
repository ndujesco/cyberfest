from urllib.parse import urlencode, urlparse

from core.http_client import DualClient
from core.session import Session
from core.finding import Finding, Severity

_ATTACKER = "https://attacker.example.com/catch"


class RedirectURITester:
    def __init__(self, client: DualClient, session: Session):
        self.client = client
        self.session = session

    async def run(self, config: dict | None = None) -> list[Finding]:
        endpoint = (config or {}).get("authorization_endpoint", "/oauth/authorize")
        findings: list[Finding] = []

        for test in (self._open_redirect, self._path_traversal, self._subdomain):
            f = await test(endpoint)
            if f:
                findings.append(f)

        return findings

    async def _open_redirect(self, endpoint: str) -> Finding | None:
        params = urlencode({
            "response_type": "code", "client_id": "test",
            "redirect_uri": _ATTACKER, "state": "specter_test",
        })
        try:
            resp = await self.client.get_anon(f"{endpoint}?{params}")
            loc = resp.headers.get("location", "")
            if resp.status_code in (301, 302, 303) and "attacker.example.com" in loc:
                return Finding(
                    module="token", severity=Severity.CRITICAL,
                    title="redirect_uri accepts arbitrary domains — auth code theft possible",
                    endpoint=endpoint,
                    evidence=f"Server redirected to {loc[:100]}",
                    cwe="CWE-601",
                )
            if resp.status_code not in (400, 401, 403, 422, 404):
                return Finding(
                    module="token", severity=Severity.MEDIUM,
                    title="redirect_uri validation possibly insufficient",
                    endpoint=endpoint,
                    evidence=f"Arbitrary redirect_uri returned HTTP {resp.status_code} (expected 400/403). Manual verification required.",
                    cwe="CWE-601",
                )
        except Exception:
            pass
        return None

    async def _path_traversal(self, endpoint: str) -> Finding | None:
        base = self.client.target
        for redir in [f"{base}/callback/../evil", f"{base}/callback/%2F..%2Fevil"]:
            params = urlencode({
                "response_type": "code", "client_id": "test",
                "redirect_uri": redir, "state": "specter_test",
            })
            try:
                resp = await self.client.get_anon(f"{endpoint}?{params}")
                if resp.status_code not in (400, 401, 403, 422, 404):
                    return Finding(
                        module="token", severity=Severity.HIGH,
                        title="redirect_uri path traversal not rejected",
                        endpoint=endpoint,
                        evidence=f"Traversal URI returned HTTP {resp.status_code}. Tested: {redir[:80]}",
                        cwe="CWE-22",
                    )
            except Exception:
                pass
        return None

    async def _subdomain(self, endpoint: str) -> Finding | None:
        parsed = urlparse(self.client.target)
        evil = f"{parsed.scheme}://evil.{parsed.netloc}/callback"
        params = urlencode({
            "response_type": "code", "client_id": "test",
            "redirect_uri": evil, "state": "specter_test",
        })
        try:
            resp = await self.client.get_anon(f"{endpoint}?{params}")
            loc = resp.headers.get("location", "")
            if resp.status_code in (301, 302, 303) and "evil." in loc:
                return Finding(
                    module="token", severity=Severity.HIGH,
                    title="redirect_uri accepts wildcard subdomain",
                    endpoint=endpoint,
                    evidence=f"Subdomain {evil} was accepted by auth server. Attacker can register this subdomain.",
                    cwe="CWE-601",
                )
        except Exception:
            pass
        return None
