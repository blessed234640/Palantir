from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
from app.providers.ollama import OllamaProvider
from fastapi.responses import StreamingResponse

app = FastAPI(title="шлюз")
provider = OllamaProvider(base_url="http://localhost:11434")

@app.post("/v1/chat/completions")

async def chat_completions(request: ChatCompletionRequest):
    payload = request.model_dump()
    if request.stream:
        return StreamingResponse(provider.chat_stream(payload), media_type="text/event-stream")
    return await provider.chat(payload)