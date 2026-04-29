import hashlib
import base64
import os
from urllib.parse import urlencode

from core.http_client import DualClient
from core.session import Session
from core.finding import Finding, Severity


def _make_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()


def _make_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class PKCETester:
    def __init__(self, client: DualClient, session: Session):
        self.client = client
        self.session = session

    async def run(self, config: dict | None = None) -> list[Finding]:
        endpoint = (config or {}).get("authorization_endpoint", "/oauth/authorize")
        token_endpoint = (config or {}).get("token_endpoint", "/oauth/token")
        findings: list[Finding] = []

        for test in (
            self._pkce_missing,
            self._plain_downgrade,
            self._token_endpoint_skip,
        ):
            f = await test(endpoint, token_endpoint)
            if f:
                findings.append(f)

        return findings

    async def _pkce_missing(self, endpoint: str, _token: str) -> Finding | None:
        params = urlencode({
            "response_type": "code",
            "client_id": "test",
            "redirect_uri": f"{self.client.target}/callback",
            "state": "specter_pkce_test",
        })
        try:
            resp = await self.client.get_anon(f"{endpoint}?{params}")
            if resp.status_code not in (400, 401, 403, 422):
                return Finding(
                    module="token",
                    severity=Severity.HIGH,
                    title="PKCE not enforced — authorization code interception risk",
                    endpoint=endpoint,
                    evidence=(
                        f"Auth request without code_challenge returned HTTP {resp.status_code}. "
                        "Server should reject with 400 when PKCE is absent."
                    ),
                    cwe="CWE-303",
                )
        except Exception:
            pass
        return None

    async def _plain_downgrade(self, endpoint: str, _token: str) -> Finding | None:
        verifier = _make_verifier()
        params = urlencode({
            "response_type": "code",
            "client_id": "test",
            "redirect_uri": f"{self.client.target}/callback",
            "state": "specter_plain_test",
            "code_challenge": verifier,
            "code_challenge_method": "plain",
        })
        try:
            resp = await self.client.get_anon(f"{endpoint}?{params}")
            if resp.status_code not in (400, 401, 403, 422):
                return Finding(
                    module="token",
                    severity=Severity.MEDIUM,
                    title="PKCE plain method accepted — S256 downgrade possible",
                    endpoint=endpoint,
                    evidence=(
                        f"code_challenge_method=plain returned HTTP {resp.status_code}. "
                        "Server should require S256 to prevent verifier exposure."
                    ),
                    cwe="CWE-326",
                )
        except Exception:
            pass
        return None

    async def _token_endpoint_skip(self, _auth: str, token_endpoint: str) -> Finding | None:
        data = {
            "grant_type": "authorization_code",
            "code": "specter_fake_code_12345",
            "redirect_uri": f"{self.client.target}/callback",
            "client_id": "test",
        }
        try:
            resp = await self.client.get_anon(token_endpoint)
            if resp.status_code == 405:
                resp = await self.client._anon.post(
                    self.client._url(token_endpoint), data=data
                )
            if resp.status_code not in (400, 401, 403, 422, 404):
                return Finding(
                    module="token",
                    severity=Severity.MEDIUM,
                    title="Token endpoint may not validate PKCE verifier",
                    endpoint=token_endpoint,
                    evidence=(
                        f"Token exchange without code_verifier returned HTTP {resp.status_code} "
                        "(expected 400). Verify server checks verifier against stored challenge."
                    ),
                    cwe="CWE-303",
                )
        except Exception:
            pass
        return None
