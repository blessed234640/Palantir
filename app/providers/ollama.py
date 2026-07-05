import httpx
from fastapi import HTTPException

class OllamaProvider():
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def chat(self, payload: dict) -> dict:
        url = url = f"{self.base_url}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError:
                raise HTTPException(status_code=502, detail=f"upstream error: {resp.text}")
            except httpx.RequestError:
                raise HTTPException(status_code=503, detail="Ollama unavailable")