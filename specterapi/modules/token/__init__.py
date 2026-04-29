from core.session import Session
from core.http_client import DualClient
from core.finding import Finding
from core import output as out

from .discovery import OAuthDiscovery
from .redirect_uri import RedirectURITester
from .pkce import PKCETester


class TokenModule:
    NAME = "token"

    def __init__(self, session: Session, client: DualClient):
        self.session = session
        self.client = client

    async def run(self) -> list[Finding]:
        out.info("[bold]TOKEN[/] — OAuth 2.0 attack surface analysis")

        discovery = OAuthDiscovery(self.client)
        config = await discovery.probe()
        endpoints = await discovery.find_auth_endpoints()

        if config:
            out.success(f"OIDC discovery found: {len(config)} keys")
        if endpoints:
            out.info(f"Active OAuth endpoints: {list(endpoints.keys())}")

        findings: list[Finding] = []

        for tester_cls in (RedirectURITester, PKCETester):
            tester = tester_cls(self.client, self.session)
            results = await tester.run(config)
            for f in results:
                self.session.add_finding(f)
                findings.append(f)
                out.finding(f)

        if not findings:
            out.info("No OAuth issues confirmed in automated pass (manual review recommended)")

        return findings
