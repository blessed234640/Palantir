import httpx
from app.reliability import retry_request

class OllamaProvider():

    
    async def chat_stream(self, payload: dict):
        model = payload.get("model") or self.model
        if not self.supports_model(model):
            model = self.model
        body = {**payload, "model": model}  
        url = f"{self.base_url}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=body) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk


    def __init__(self, base_url: str, model: str = "phi4-mini"):
        self.base_url = base_url
        self.model = model
        

    async def chat(self, payload: dict) -> dict:
        model = payload.get("model") or self.model
        if not self.supports_model(model):
            model = self.model
        body = {**payload, "model": model}
        url = f"{self.base_url}/v1/chat/completions"

        async def do_request():                     # один вызов, без ретраев
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=body)
                resp.raise_for_status()
                return resp.json()

        return await retry_request(do_request)       # обёртка гоняет его с ретраями

    
    def supports_model(self, model: str) -> bool:
        return not model.startswith("gemini")