#!/usr/bin/env python3
import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console

from core.session import Session
from core.http_client import DualClient
from core import output as out

console = Console()


def _make_client(target, user_a, user_b, proxy, delay, timeout):
    return DualClient(
        target=target,
        user_a_token=user_a,
        user_b_token=user_b,
        proxy=proxy,
        delay=delay,
        timeout=timeout,
    )


def _save_json(findings, path):
    data = [
        {
            "id": f.id,
            "module": f.module,
            "severity": f.severity.value,
            "title": f.title,
            "endpoint": f.endpoint,
            "evidence": f.evidence,
            "cwe": f.cwe,
            "cvss": f.cvss,
        }
        for f in findings
    ]
    Path(path).write_text(json.dumps(data, indent=2))
    out.success(f"JSON report saved → {path}")


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def cli(ctx):
    """SpecterAPI — API Security Scanner"""
    if ctx.invoked_subcommand is None:
        out.print_banner()
        from core.repl import Repl
        asyncio.run(Repl().run())


@cli.command()
@click.option("-t", "--target", required=True, help="Target base URL")
@click.option("--depth", default=2, show_default=True, help="Crawl depth")
@click.option("--probe", is_flag=True, default=False, help="Probe discovered endpoints")
@click.option("--wordlist", default=None, help="Custom wordlist path")
@click.option("--proxy", default=None, help="HTTP proxy (e.g. http://127.0.0.1:8080)")
@click.option("--delay", default=0.0, help="Delay between requests (seconds)")
@click.option("--timeout", default=15.0, help="Request timeout (seconds)")
@click.option("--output", default="table", type=click.Choice(["table", "json", "pdf"]), help="Output format")
@click.option("--out-file", default=None, help="Output file path")
def ghost(target, depth, probe, wordlist, proxy, delay, timeout, output, out_file):
    """Discover hidden API endpoints from JS bundles."""
    out.print_banner()
    session = Session(target=target)
    client = _make_client(target, None, None, proxy, delay, timeout)

    async def _run():
        from modules.ghost import GhostModule
        async with client:
            module = GhostModule(session, client)
            findings = await module.run(depth=depth, probe=probe)
        return findings

    findings = asyncio.run(_run())
    out.findings_summary(session.get_findings())

    if output == "json":
        path = out_file or f"specter_ghost_{session.id[:8]}.json"
        _save_json(findings, path)
    elif output == "pdf":
        from reports.pdf_renderer import render_pdf
        path = render_pdf(session, out_file)
        out.success(f"PDF report saved → {path}")


@cli.command()
@click.option("-t", "--target", required=True, help="Target base URL")
@click.option("--proxy", default=None, help="HTTP proxy")
@click.option("--delay", default=0.0, help="Delay between requests (seconds)")
@click.option("--timeout", default=15.0, help="Request timeout (seconds)")
@click.option("--output", default="table", type=click.Choice(["table", "json", "pdf"]))
@click.option("--out-file", default=None, help="Output file path")
def token(target, proxy, delay, timeout, output, out_file):
    """Test OAuth 2.0 / OIDC attack surface."""
    out.print_banner()
    session = Session(target=target)
    client = _make_client(target, None, None, proxy, delay, timeout)

    async def _run():
        from modules.token import TokenModule
        async with client:
            module = TokenModule(session, client)
            return await module.run()

    findings = asyncio.run(_run())
    out.findings_summary(session.get_findings())

    if output == "json":
        path = out_file or f"specter_token_{session.id[:8]}.json"
        _save_json(findings, path)
    elif output == "pdf":
        from reports.pdf_renderer import render_pdf
        path = render_pdf(session, out_file)
        out.success(f"PDF report saved → {path}")


@cli.command()
@click.option("-t", "--target", required=True, help="Target base URL")
@click.option("--user-a", required=True, help="User A (victim) Bearer token")
@click.option("--user-b", required=True, help="User B (attacker) Bearer token")
@click.option("--session", "session_id", default=None, help="Resume a specific session ID (uses its endpoints)")
@click.option("--proxy", default=None, help="HTTP proxy")
@click.option("--delay", default=0.0, help="Delay between requests (seconds)")
@click.option("--timeout", default=15.0, help="Request timeout (seconds)")
@click.option("--output", default="table", type=click.Choice(["table", "json", "pdf"]))
@click.option("--out-file", default=None, help="Output file path")
def idor(target, user_a, user_b, session_id, proxy, delay, timeout, output, out_file):
    """Test for BOLA/IDOR across dual user sessions."""
    out.print_banner()
    if session_id:
        session = Session.load(session_id)
        out.info(f"Loaded session [cyan]{session_id[:8]}[/] ({len(session.get_endpoints())} endpoints)")
    else:
        session = Session.find_latest(target)
        if session:
            ep_count = len(session.get_endpoints())
            out.info(f"Auto-loaded session [cyan]{session.id[:8]}[/] with {ep_count} endpoint(s) from ghost run")
        else:
            out.warn("No prior ghost session found for this target — creating a new session (no endpoints)")
            session = Session(target=target)
    client = _make_client(target, user_a, user_b, proxy, delay, timeout)

    async def _run():
        from modules.idor import IDORModule
        async with client:
            module = IDORModule(session, client)
            return await module.run()

    findings = asyncio.run(_run())
    out.findings_summary(session.get_findings())

    if output == "json":
        path = out_file or f"specter_idor_{session.id[:8]}.json"
        _save_json(findings, path)
    elif output == "pdf":
        from reports.pdf_renderer import render_pdf
        path = render_pdf(session, out_file)
        out.success(f"PDF report saved → {path}")


@cli.command()
@click.option("-t", "--target", required=True, help="Target base URL")
@click.option("--user-a", default=None, help="User A Bearer token (for IDOR)")
@click.option("--user-b", default=None, help="User B Bearer token (for IDOR)")
@click.option("--depth", default=2, show_default=True, help="Ghost crawl depth")
@click.option("--probe", is_flag=True, default=True, help="Probe discovered endpoints")
@click.option("--proxy", default=None, help="HTTP proxy")
@click.option("--delay", default=0.5, show_default=True, help="Delay between requests")
@click.option("--timeout", default=15.0, help="Request timeout (seconds)")
@click.option("--output", default="table", type=click.Choice(["table", "json", "pdf"]))
@click.option("--out-file", default=None, help="Output file path")
def chain(target, user_a, user_b, depth, probe, proxy, delay, timeout, output, out_file):
    """Run ghost → token → idor in sequence (full attack chain)."""
    out.print_banner()
    out.info(f"[bold cyan]CHAIN[/] — full attack chain against {target}")
    session = Session(target=target)
    client = _make_client(target, user_a, user_b, proxy, delay, timeout)

    async def _run():
        all_findings = []
        async with client:
            from modules.ghost import GhostModule
            from modules.token import TokenModule
            from modules.idor import IDORModule

            out.info("[1/3] Ghost — endpoint discovery")
            ghost_mod = GhostModule(session, client)
            all_findings.extend(await ghost_mod.run(depth=depth, probe=probe))

            out.info("[2/3] Token — OAuth analysis")
            token_mod = TokenModule(session, client)
            all_findings.extend(await token_mod.run())

            if user_a and user_b:
                out.info("[3/3] IDOR — BOLA detection")
                idor_mod = IDORModule(session, client)
                all_findings.extend(await idor_mod.run())
            else:
                out.warn("[3/3] IDOR skipped — provide --user-a and --user-b for BOLA testing")

        return all_findings

    findings = asyncio.run(_run())
    out.findings_summary(session.get_findings())

    if output == "json":
        path = out_file or f"specter_chain_{session.id[:8]}.json"
        _save_json(findings, path)
    elif output == "pdf":
        from reports.pdf_renderer import render_pdf
        path = render_pdf(session, out_file)
        out.success(f"PDF report saved → {path}")


@cli.command("sessions")
def list_sessions():
    """List saved sessions."""
    sessions = Session.list_sessions()
    if not sessions:
        out.warn("No sessions found.")
        return
    console.print(f"\n[bold]Saved Sessions[/] ({len(sessions)} total)\n")
    for s in sessions:
        console.print(
            f"  [cyan]{s['id'][:8]}[/]  {s['target']:<40}  "
            f"[dim]{s['created_at']}[/]  "
            f"findings=[yellow]{s['findings']}[/]"
        )
    console.print()


if __name__ == "__main__":
    cli()
