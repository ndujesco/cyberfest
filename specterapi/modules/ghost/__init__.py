import asyncio

from rich.progress import Progress, SpinnerColumn, TextColumn

from core.session import Session
from core.http_client import DualClient
from core import output as out
from .crawler import Crawler
from .regex_sweep import RegexSweep
from .prober import Prober


class GhostModule:
    NAME = "ghost"

    def __init__(self, session: Session, client: DualClient):
        self.session = session
        self.client = client

    async def run(self, depth: int = 3, probe: bool = True):
        out.info(f"[bold]Ghost[/] — crawling [cyan]{self.client.target}[/]")

        js_urls = await Crawler(self.client).collect(depth=depth)
        if not js_urls:
            out.warn("No JS bundles found — target may require authentication or is not a SPA")
            return
        out.success(f"Found {len(js_urls)} JS chunk(s)")

        sweeper = RegexSweep()
        all_candidates: list[dict] = []

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as prog:
            task = prog.add_task("Extracting endpoint candidates…", total=len(js_urls))
            for url in js_urls:
                try:
                    resp = await self.client.get_anon(url)
                    if resp.status_code == 200:
                        all_candidates.extend(sweeper.extract(resp.text, source=url))
                except Exception:
                    pass
                prog.advance(task)

        # Deduplicate preserving highest-priority order
        seen: set[tuple] = set()
        unique: list[dict] = []
        for c in sorted(all_candidates, key=lambda x: x.get("priority", 0), reverse=True):
            key = (c["path"], c["method"])
            if key not in seen:
                seen.add(key)
                unique.append(c)

        out.success(f"Extracted {len(unique)} unique endpoint candidate(s)")

        if not probe:
            for c in unique:
                self.session.add_endpoint(path=c["path"], method=c["method"], source_file=c.get("source"))
            return

        findings = await Prober(self.client, self.session).probe_all(unique)
        for f in findings:
            self.session.add_finding(f)
            out.finding(f)

        eps = self.session.get_endpoints()
        unauth = [e for e in eps if not e.get("auth_required", 1)]
        out.success(
            f"Probed {len(eps)} endpoint(s) — "
            f"[bold red]{len(unauth)} unauthenticated[/] — "
            f"{len(findings)} finding(s)"
        )
        if eps:
            out.endpoints_table(eps[:40])
