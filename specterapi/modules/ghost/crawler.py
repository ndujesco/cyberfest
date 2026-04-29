import asyncio
import re
from urllib.parse import urljoin, urlparse

from core.http_client import DualClient

_JS_SRC = re.compile(r'src=["\']([^"\']+\.js[^"\']*)["\']', re.IGNORECASE)
_SCRIPT_TAG = re.compile(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', re.IGNORECASE)
_CHUNK = re.compile(r'["\'](\/(static|assets|js)[^"\']*\d+[^"\']*\.js[^"\']*)["\']')
_LINK = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)

_SKIP_EXT = (".css", ".png", ".jpg", ".jpeg", ".ico", ".svg", ".woff", ".woff2", ".ttf", ".gif")


class Crawler:
    def __init__(self, client: DualClient):
        self.client = client
        self.base = client.target
        self._origin = urlparse(self.base).netloc

    async def collect(self, depth: int = 3) -> list[str]:
        js_urls: set[str] = set()
        to_crawl: set[str] = {self.base}
        crawled: set[str] = set()

        for _ in range(depth):
            batch = list(to_crawl - crawled)[:8]
            if not batch:
                break
            crawled.update(batch)

            results = await asyncio.gather(
                *[self._fetch(url) for url in batch], return_exceptions=True
            )
            for result in results:
                if isinstance(result, Exception):
                    continue
                new_links, new_js = result
                js_urls.update(new_js)
                to_crawl.update(new_links - crawled)

        return list(js_urls)

    async def _fetch(self, url: str) -> tuple[set[str], set[str]]:
        try:
            resp = await self.client.get_anon(url)
            html = resp.text
        except Exception:
            return set(), set()

        links: set[str] = set()
        js: set[str] = set()

        for pattern in (_JS_SRC, _SCRIPT_TAG, _CHUNK):
            for match in pattern.findall(html):
                href = match if isinstance(match, str) else match[0]
                abs_url = self._abs(href)
                if abs_url and self._same_origin(abs_url):
                    js.add(abs_url)

        for match in _LINK.findall(html):
            abs_url = self._abs(match)
            if abs_url and self._same_origin(abs_url):
                if not any(abs_url.endswith(ext) for ext in _SKIP_EXT):
                    links.add(abs_url)

        return links, js

    def _abs(self, href: str) -> str:
        if not href:
            return ""
        href = href.strip()
        if href.startswith("//"):
            return f"{urlparse(self.base).scheme}:{href}"
        if href.startswith("http"):
            return href
        return urljoin(self.base, href)

    def _same_origin(self, url: str) -> bool:
        host = urlparse(url).netloc
        return not host or host == self._origin
