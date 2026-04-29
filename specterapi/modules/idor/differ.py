import json


class Differ:
    """Compare User A's and User B's responses to detect BOLA."""

    def compare(self, resp_a: dict, resp_b: dict, obj: dict) -> dict | None:
        sa, sb = resp_a.get("status", 0), resp_b.get("status", 0)
        sza, szb = resp_a.get("size", 0), resp_b.get("size", 0)
        ba, bb = resp_a.get("body", ""), resp_b.get("body", "")
        endpoint = obj.get("endpoint", "?")
        obj_id = obj.get("object_id", "?")

        # Both users got a successful response and bodies look similar
        if sa in (200, 201) and sb in (200, 201) and szb > 50:
            sim = self._similarity(ba, bb)
            if sim > 0.5 or szb > sza * 0.7:
                return {
                    "type": "read_bola",
                    "evidence": (
                        f"User B (HTTP {sb}, {szb:,}B) accessed User A's resource "
                        f"at {endpoint} (object_id={obj_id}). "
                        f"Body similarity: {sim:.0%}."
                    ),
                }

        # User B successfully deleted User A's resource
        if obj.get("method") == "DELETE" and sa in (200, 204) and sb in (200, 204):
            return {
                "type": "delete_bola",
                "evidence": (
                    f"User B DELETE {endpoint} succeeded (HTTP {sb}). "
                    "Cross-user destructive BOLA confirmed."
                ),
            }

        # Unexpected success for User B when User A was blocked
        if sb in (200, 201) and sa in (401, 403):
            return {
                "type": "auth_bypass",
                "evidence": (
                    f"User B got HTTP {sb} on {endpoint} while User A got {sa}. "
                    "Possible privilege escalation."
                ),
            }

        return None

    def _similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        try:
            ka = set(self._keys(json.loads(a)))
            kb = set(self._keys(json.loads(b)))
            if not ka:
                return 0.0
            return len(ka & kb) / max(len(ka), len(kb))
        except (ValueError, json.JSONDecodeError):
            wa = set(a.lower().split())
            wb = set(b.lower().split())
            if not wa:
                return 0.0
            return len(wa & wb) / max(len(wa), len(wb))

    def _keys(self, obj, depth: int = 0) -> list[str]:
        if depth > 3:
            return []
        keys: list[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.append(k)
                keys.extend(self._keys(v, depth + 1))
        elif isinstance(obj, list) and obj:
            keys.extend(self._keys(obj[0], depth + 1))
        return keys
