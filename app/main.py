from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
from app.providers.ollama import OllamaProvider

app = FastAPI(title="шлюз")
provider = OllamaProvider(base_url="http://localhost:11434")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    payload = request.model_dump()
    return await provider.chat(payload)
   