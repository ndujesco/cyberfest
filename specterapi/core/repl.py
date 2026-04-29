import asyncio
import shlex

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from . import output as out

_STYLE = Style.from_dict({"": "#cdd9e5"})

_GLOBAL = ["use", "sessions", "load", "chain", "report", "exit", "back", "help", "clear", "options", "set", "show", "run"]
_MODULES = ["ghost", "token", "idor"]

_HELP = """\
[bold]Global commands[/]
  [cyan]use <module>[/]       load a module: ghost | token | idor
  [cyan]set <opt> <val>[/]    set an option (target, depth, user-a, user-b, proxy, delay)
  [cyan]options[/]            show current options
  [cyan]run[/]                execute the active module
  [cyan]chain[/]              run Ghost → Token → IDOR in sequence
  [cyan]report [pdf|json][/]  generate report from current session
  [cyan]show endpoints[/]     list discovered endpoints
  [cyan]show findings[/]      list all findings
  [cyan]sessions[/]           list saved sessions
  [cyan]load <id>[/]          resume a saved session
  [cyan]back[/]               return to main prompt
  [cyan]exit[/]               quit SpecterAPI
"""


class Repl:
    def __init__(self):
        self.module: str | None = None
        self.session = None
        self.opts: dict[str, str] = {}

    def _prompt(self):
        if self.module:
            return HTML(f'<ansigreen>specter</ansigreen>[<ansiyellow>{self.module}</ansiyellow>] <ansigreen>&gt;</ansigreen> ')
        return HTML("<ansigreen>specter &gt;</ansigreen> ")

    def _completer(self):
        module_cmds = {
            "ghost": ["run", "crawl", "extract", "probe", "sourcemap", "show"],
            "token": ["run", "discover", "redirect-uri", "pkce", "state", "show"],
            "idor":  ["run", "record", "replay", "horizontal", "vertical", "graphql", "show"],
        }
        extra = module_cmds.get(self.module, []) if self.module else _MODULES
        return WordCompleter(_GLOBAL + extra, ignore_case=True)

    async def run(self):
        ps = PromptSession(style=_STYLE)
        while True:
            try:
                raw = await ps.prompt_async(self._prompt(), completer=self._completer())
            except (EOFError, KeyboardInterrupt):
                out.info("Goodbye.")
                break
            raw = raw.strip()
            if not raw:
                continue
            try:
                args = shlex.split(raw)
            except ValueError:
                args = raw.split()
            await self._dispatch(args[0].lower(), args[1:])

    async def _dispatch(self, cmd: str, args: list[str]):
        if cmd in ("exit", "quit"):
            raise SystemExit(0)

        elif cmd == "back":
            self.module = None

        elif cmd == "clear":
            import os; os.system("clear")
            out.print_banner()

        elif cmd == "help":
            out.console.print(_HELP)

        elif cmd == "use":
            if args and args[0] in _MODULES:
                self.module = args[0]
                out.info(f"Module [bold]{args[0]}[/] loaded. Type [bold]options[/] or [bold]run[/].")
            else:
                out.error(f"Unknown module. Choose from: {', '.join(_MODULES)}")

        elif cmd == "set":
            if len(args) < 2:
                out.error("Usage: set <option> <value>")
            else:
                key, val = args[0].lower(), " ".join(args[1:])
                self.opts[key] = val
                out.success(f"{key} => {val}")

        elif cmd == "options":
            self._print_options()

        elif cmd == "sessions":
            from .session import Session
            for s in Session.list_sessions():
                out.info(f"[bold]{s['id']}[/] — {s['target']} — {s['findings']} findings, {s['endpoints']} endpoints")

        elif cmd == "load":
            if not args:
                out.error("Usage: load <session_id>")
                return
            try:
                from .session import Session
                self.session = Session.load(args[0])
                out.success(f"Session [bold]{args[0]}[/] loaded — target: {self.session.target}")
            except FileNotFoundError as e:
                out.error(str(e))

        elif cmd == "run":
            await self._run_module()

        elif cmd == "chain":
            await self._run_chain()

        elif cmd == "report":
            await self._run_report(args)

        elif cmd == "show":
            self._show(args[0] if args else "")

        else:
            out.error(f"Unknown command: {cmd}. Type [bold]help[/].")

    async def _make_context(self):
        from .session import Session
        from .http_client import DualClient

        target = self.opts.get("target", "")
        if not target:
            out.error("target not set. Use: set target <url>")
            return None, None

        sess = self.session or Session(target=target)
        sess.target = target

        client = DualClient(
            target=target,
            user_a_token=self.opts.get("user-a"),
            user_b_token=self.opts.get("user-b"),
            proxy=self.opts.get("proxy"),
            delay=float(self.opts.get("delay", 0)),
        )
        return sess, client

    async def _run_module(self):
        if not self.module:
            out.error("No module loaded. Use: use ghost | token | idor")
            return
        sess, client = await self._make_context()
        if not sess:
            return
        try:
            if self.module == "ghost":
                from modules.ghost import GhostModule
                await GhostModule(sess, client).run(
                    depth=int(self.opts.get("depth", 3)),
                    probe=self.opts.get("probe", "true").lower() != "false",
                )
            elif self.module == "token":
                from modules.token import TokenModule
                await TokenModule(sess, client).run()
            elif self.module == "idor":
                from modules.idor import IDORModule
                await IDORModule(sess, client).run()
            out.findings_summary(sess.get_findings())
        finally:
            await client.aclose()
        self.session = sess

    async def _run_chain(self):
        sess, client = await self._make_context()
        if not sess:
            return
        try:
            from modules.ghost import GhostModule
            from modules.token import TokenModule
            from modules.idor import IDORModule
            out.info(f"[bold]Chain[/] — session [bold]{sess.id}[/]")
            await GhostModule(sess, client).run()
            await TokenModule(sess, client).run()
            await IDORModule(sess, client).run()
            out.findings_summary(sess.get_findings())
        finally:
            await client.aclose()
        self.session = sess

    async def _run_report(self, args: list[str]):
        if not self.session:
            out.error("No active session. Run a scan first.")
            return
        fmt = args[0] if args else "pdf"
        if fmt == "pdf":
            try:
                from reports.pdf_renderer import generate_pdf
                path = generate_pdf(self.session)
                out.success(f"PDF saved: {path}")
            except Exception as e:
                out.error(f"PDF failed: {e}")
        elif fmt == "json":
            import json
            path = f"specter_{self.session.id}.json"
            with open(path, "w") as fp:
                json.dump([{
                    "id": f.id, "module": f.module, "severity": f.severity.value,
                    "title": f.title, "endpoint": f.endpoint, "evidence": f.evidence,
                    "cvss": f.cvss, "cwe": f.cwe,
                } for f in self.session.get_findings()], fp, indent=2)
            out.success(f"JSON saved: {path}")

    def _show(self, what: str):
        if not self.session:
            out.error("No active session.")
            return
        if what in ("endpoints", "ep"):
            out.endpoints_table(self.session.get_endpoints())
        elif what in ("findings", "f"):
            for f in self.session.get_findings():
                out.finding(f)
        else:
            out.info("Usage: show endpoints | show findings")

    def _print_options(self):
        from rich.table import Table
        from rich import box
        defaults = {"target": "", "depth": "3", "probe": "true",
                    "user-a": "", "user-b": "", "proxy": "", "delay": "0"}
        t = Table(box=box.SIMPLE)
        t.add_column("Option", style="bold cyan")
        t.add_column("Value")
        t.add_column("Required", style="dim")
        required = {"target"}
        for k, default in defaults.items():
            val = self.opts.get(k, default)
            req = "[bold red]yes[/]" if k in required else "no"
            t.add_row(k, val or "[dim]not set[/]", req)
        out.console.print(t)
