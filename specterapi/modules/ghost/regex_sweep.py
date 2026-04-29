import re
from urllib.parse import urlparse

_HIGH_VALUE_KW = {"admin", "debug", "internal", "config", "secret", "token", "key",
                  "password", "user", "export", "dump", "backup", "manage"}

_SKIP = [
    re.compile(r"^\/(static|assets|images|fonts|css|img|icons|media)"),
    re.compile(r"\.(png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|css|map)$"),
    re.compile(r"^\/[a-z]{2}(-[A-Z]{2})?\/"),           # locale prefix /en/, /en-US/
    re.compile(r"^\/\d{4}\/"),                           # date paths
]

_API_RE = re.compile(
    r"\/(api|v\d+|graphql|admin|internal|debug|rest|auth|user|account|order|payment|webhook)",
    re.IGNORECASE,
)

_PATTERNS: list[tuple[str, re.Pattern]] = [
    # axios.get('/path'), axios.post('/path')
    ("GET",    re.compile(r"""axios\.get\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    ("POST",   re.compile(r"""axios\.post\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    ("PUT",    re.compile(r"""axios\.put\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    ("DELETE", re.compile(r"""axios\.delete\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    ("PATCH",  re.compile(r"""axios\.patch\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    # fetch('/path')
    ("GET",    re.compile(r"""fetch\s*\(\s*["`'](\/[^"`'\s]{3,80})["`']""")),
    # template literals `/api/...`
    ("GET",    re.compile(r"""`(\/api\/[^`\s]{3,80})`""")),
    ("GET",    re.compile(r"""`(\/v\d+\/[^`\s]{3,80})`""")),
    # string assignments: url = '/api/...'
    ("GET",    re.compile(r"""(?:url|path|endpoint|route|API_URL)\s*[:=]\s*["`'](\/[^"`'\s?#]{4,60})["`']""")),
    # generic API string literals
    ("GET",    re.compile(r"""["`'](\/(?:api|v\d+|graphql|admin|internal|debug)\/[^"`'\s?#]{2,60})["`']""")),
]


class RegexSweep:
    def extract(self, js: str, source: str = "") -> list[dict]:
        seen: set[str] = set()
        results: list[dict] = []
        short_src = self._short(source)

        for method, pattern in _PATTERNS:
            for match in pattern.findall(js):
                path = self._normalize(match)
                if not path or path in seen or not self._valid(path):
                    continue
                seen.add(path)
                results.append({
                    "path": path,
                    "method": method,
                    "source": short_src,
                    "priority": self._priority(path),
                })

        results.sort(key=lambda x: x["priority"], reverse=True)
        return results

    def _normalize(self, path: str) -> str:
        path = path.strip().split("?")[0].split("#")[0]
        if not path.startswith("/"):
            try:
                parsed = urlparse(path)
                path = parsed.path or ""
            except Exception:
                return ""
        return path

    def _valid(self, path: str) -> bool:
        if len(path) < 5 or len(path) > 100:
            return False
        for skip in _SKIP:
            if skip.search(path):
                return False
        return bool(_API_RE.search(path))

    def _priority(self, path: str) -> int:
        pl = path.lower()
        score = sum(2 for kw in _HIGH_VALUE_KW if kw in pl)
        if re.search(r"\{[^}]+\}|:\w+|\/\d+", path):
            score += 1
        return score

    def _short(self, url: str) -> str:
        if not url:
            return ""
        parts = url.split("/")
        return "/".join(parts[-2:]) if len(parts) > 2 else url
