import httpx


class LogseqClient:
    def __init__(
        self,
        token: str,
        host: str = "127.0.0.1",
        port: int = 12315,
        protocol: str = "http",
    ) -> None:
        self._base_url = f"{protocol}://{host}:{port}/api"
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        self._client = httpx.AsyncClient(timeout=10.0)

    async def call_logseq_api(self, method: str, args: list) -> object:
        response = await self._client.post(
            self._base_url,
            headers=self._headers,
            json={"method": method, "args": args},
        )
        response.raise_for_status()
        return response.json()
