from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
import httpx
from fastapi import HTTPException

app = FastAPI(title="шлюз")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    url = "http://localhost:11434/v1/chat/completions"
    payload = request.model_dump()
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=502, detail=f"upstream error: {resp.text}")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Ollama unavailable")
   