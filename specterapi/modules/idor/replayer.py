from core.http_client import DualClient


class Replayer:
    def __init__(self, client: DualClient):
        self.client = client

    async def replay_b(self, path: str, method: str = "GET") -> dict:
        try:
            if method == "GET":
                resp = await self.client.get_b(path)
            else:
                resp = await self.client.request_b(method, path)
            return {
                "status": resp.status_code,
                "body": resp.text[:4000],
                "size": len(resp.content),
                "headers": dict(resp.headers),
            }
        except Exception as e:
            return {"status": 0, "body": str(e), "size": 0, "headers": {}}
