from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .finding import Finding, Severity

console = Console()

_LABEL = {
    Severity.CRITICAL: "[bold white on red] CRITICAL [/]",
    Severity.HIGH:     "[bold red] HIGH [/]",
    Severity.MEDIUM:   "[bold yellow] MEDIUM [/]",
    Severity.LOW:      "[bold green] LOW [/]",
    Severity.INFO:     "[bold blue] INFO [/]",
}

_STYLE = {
    Severity.CRITICAL: "bold white on red",
    Severity.HIGH:     "bold red",
    Severity.MEDIUM:   "bold yellow",
    Severity.LOW:      "bold green",
    Severity.INFO:     "bold blue",
}

BANNER = """\
[bold green]                                    __  _____  ____[/]
[bold green]   _________  ___  _____/ /_____  / / / /  _/ __ )[/]
[bold green]  / ___/ __ \\/ _ \\/ ___/ __/ _ \\/ /_/ // // __  |[/]
[bold green] (__  ) /_/ /  __/ /__/ /_/  __/ __  // // /_/ /[/]
[bold green]/____/ .___/\\___/\\___/\\__/\\___/_/ /_/___/_____/[/]
[bold green]    /_/[/]  [dim]v0.1.0  ·  API attack surface suite[/]

  [dim]modules:[/] [bold magenta]ghost[/]  [bold red]token[/]  [bold blue]idor[/]   [dim]by Zer0day Saints[/]
"""


def print_banner():
    console.print(BANNER)


def info(msg: str):
    console.print(f"[dim][[/][bold blue]*[/][dim]][/] {msg}")


def success(msg: str):
    console.print(f"[dim][[/][bold green]+[/][dim]][/] {msg}")


def warn(msg: str):
    console.print(f"[dim][[/][bold yellow]![/][dim]][/] {msg}")


def error(msg: str):
    console.print(f"[dim][[/][bold red]![/][dim]][/] {msg}")


def finding(f: Finding):
    console.print(f"{_LABEL[f.severity]} [bold]{f.title}[/]")
    console.print(f"  [dim]endpoint:[/] [cyan]{f.endpoint}[/]")
    console.print(f"  [dim]evidence:[/] {f.evidence[:140]}")
    console.print()


def endpoints_table(endpoints: list[dict]):
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    t.add_column("Method", style="bold cyan", width=8)
    t.add_column("Path")
    t.add_column("Status", width=7)
    t.add_column("Auth", width=7)
    t.add_column("Size", width=9, justify="right")
    t.add_column("Source", style="dim", width=28)

    for ep in endpoints:
        s = str(ep.get("status_code") or "?")
        sc = "[green]" if s.startswith("2") else "[yellow]" if s.startswith("4") else "[red]"
        auth_req = ep.get("auth_required", 1)
        size = ep.get("response_size")
        t.add_row(
            ep.get("method", "GET"),
            ep.get("path", ""),
            f"{sc}{s}[/]",
            "[green]Yes[/]" if auth_req else "[bold red]NONE[/]",
            f"{size:,}" if size else "?",
            (ep.get("source_file") or "")[-28:],
        )
    console.print(t)


def findings_summary(findings: list[Finding]):
    counts = {s: 0 for s in Severity}
    for f in findings:
        counts[f.severity] += 1

    t = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    t.add_column("Severity", style="bold")
    t.add_column("Count", justify="right")

    for sev in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
        if counts[sev]:
            t.add_row(Text(f"  {sev.value.upper()}  ", style=_STYLE[sev]), str(counts[sev]))

    if not any(counts.values()):
        console.print("[dim]No findings.[/]")
    else:
        console.print(Panel(t, title="[bold]FINDINGS SUMMARY[/]", border_style="dim"))
