from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
import httpx
app = FastAPI(title="шлюз")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    url = "http://localhost:11434/v1/chat/completions"
    payload = request.model_dump()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=payload)
        return resp.json()
