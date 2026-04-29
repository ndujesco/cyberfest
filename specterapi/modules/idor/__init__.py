from core.session import Session
from core.http_client import DualClient
from core.finding import Finding, Severity
from core import output as out

from .recorder import Recorder
from .replayer import Replayer
from .differ import Differ


class IDORModule:
    NAME = "idor"

    def __init__(self, session: Session, client: DualClient):
        self.session = session
        self.client = client

    async def run(self, endpoints: list[dict] | None = None) -> list[Finding]:
        if not self.client.user_a_token or not self.client.user_b_token:
            out.warn("IDOR skipped — provide --user-a and --user-b tokens for BOLA testing")
            return []

        if endpoints is None:
            endpoints = self.session.get_endpoints()

        if not endpoints:
            out.warn("No endpoints to test. Run ghost first or provide endpoints.")
            return []

        out.info(f"[bold]IDOR[/] — dual-session test across {len(endpoints)} endpoint(s)")

        objects = await Recorder(self.client, self.session).record_all(endpoints)
        if not objects:
            out.warn("No object IDs captured from User A's session")
            return []

        out.success(f"Captured {len(objects)} object reference(s) from User A")

        replayer = Replayer(self.client)
        differ = Differ()
        findings: list[Finding] = []

        for obj in objects:
            resp_b = await replayer.replay_b(obj["endpoint"], obj["method"])
            verdict = differ.compare(obj["response_a"], resp_b, obj)
            if verdict:
                is_delete = verdict["type"] == "delete_bola"
                f = Finding(
                    module="idor",
                    severity=Severity.CRITICAL if is_delete else Severity.HIGH,
                    title=f"BOLA — {obj['method']} {obj['endpoint']} accessible cross-user",
                    endpoint=f"{obj['method']} {obj['endpoint']}",
                    evidence=verdict["evidence"],
                    cwe="CWE-639",
                )
                self.session.add_finding(f)
                findings.append(f)
                out.finding(f)

        if not findings:
            out.info("No BOLA confirmed in this pass (manual testing recommended)")

        return findings
