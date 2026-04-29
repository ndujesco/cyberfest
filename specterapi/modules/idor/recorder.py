import asyncio
import json
import re

from core.http_client import DualClient
from core.session import Session

_ID_IN_PATH = re.compile(r"/(\d{3,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
_ID_KEYS = {"id", "user_id", "order_id", "account_id", "doc_id", "invoice_id",
            "item_id", "product_id", "customer_id", "transaction_id"}


class Recorder:
    def __init__(self, client: DualClient, session: Session):
        self.client = client
        self.session = session

    async def record_all(self, endpoints: list[dict]) -> list[dict]:
        sem = asyncio.Semaphore(5)

        async def _one(ep):
            async with sem:
                try:
                    return await self._record(ep)
                except Exception:
                    return []

        results = await asyncio.gather(*[_one(ep) for ep in endpoints])
        return [obj for batch in results for obj in batch]

    async def _record(self, ep: dict) -> list[dict]:
        path = ep.get("path", "")
        method = ep.get("method", "GET")
        if method not in ("GET",):
            return []

        try:
            resp = await self.client.get_a(path)
        except Exception:
            return []

        if resp.status_code not in (200, 201):
            return []

        body = resp.text
        objects: list[dict] = []

        # IDs already in the path itself
        for m in _ID_IN_PATH.finditer(path):
            _add(objects, self.session, path, method, m.group(1),
                 "uuid" if "-" in m.group(1) else "integer", body, resp.status_code, len(resp.content))

        # IDs found in the response JSON
        try:
            data = resp.json()
            for obj_id, id_type in self._extract_ids(data):
                test_path = _build_path(path, obj_id)
                if test_path:
                    _add(objects, self.session, test_path, "GET", obj_id, id_type,
                         body, resp.status_code, len(resp.content))
        except (ValueError, json.JSONDecodeError):
            # Fall back to UUID regex in raw body
            for m in _UUID.finditer(body[:4000]):
                test_path = _build_path(path, m.group(0))
                if test_path:
                    _add(objects, self.session, test_path, "GET", m.group(0), "uuid",
                         body, resp.status_code, len(resp.content))

        return objects

    def _extract_ids(self, data, depth: int = 0) -> list[tuple[str, str]]:
        if depth > 3:
            return []
        ids: list[tuple[str, str]] = []
        if isinstance(data, dict):
            for k, v in data.items():
                kl = k.lower()
                if kl in _ID_KEYS or kl.endswith("_id"):
                    if isinstance(v, int) and v > 0:
                        ids.append((str(v), "integer"))
                    elif isinstance(v, str):
                        if _UUID.fullmatch(v):
                            ids.append((v, "uuid"))
                        elif v.isdigit():
                            ids.append((v, "integer"))
                else:
                    ids.extend(self._extract_ids(v, depth + 1))
        elif isinstance(data, list):
            for item in data[:5]:
                ids.extend(self._extract_ids(item, depth + 1))
        return ids


def _add(objects, session, path, method, obj_id, id_type, body, status, size):
    session.add_object(path, obj_id, id_type=id_type, raw_value=obj_id)
    objects.append({
        "endpoint": path, "method": method,
        "object_id": obj_id, "id_type": id_type,
        "response_a": {"status": status, "body": body[:4000], "size": size},
    })


def _build_path(base: str, obj_id: str) -> str:
    if _ID_IN_PATH.search(base):
        return re.sub(r"/(\d+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
                      f"/{obj_id}", base, count=1)
    return base.rstrip("/") + "/" + obj_id
