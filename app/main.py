from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
from app.providers.ollama import OllamaProvider
from fastapi.responses import StreamingResponse
from app.providers.gemini import GeminiProvider
from app.config import settings
from app.router import Router
from app.cache import InMemoryCache


app = FastAPI(title="шлюз")
provider = OllamaProvider(base_url="http://localhost:11434")
gemini = GeminiProvider(api_key=settings.gemini_api_key)
router = Router(providers=[provider, gemini])
cache = InMemoryCache(ttl_seconds=3600)

@app.post("/v1/chat/completions")

async def chat_completions(request: ChatCompletionRequest):
    payload = request.model_dump()
    if request.stream:
        return StreamingResponse(router.chat_stream(payload), media_type="text/event-stream")
    cached = cache.get(payload)
    if cached is not None:
        return {**cached, "cached": True}  # попадание — отдаём, к провайдеру не идём

    result = await router.chat(payload)     # промах — обычный путь
    cache.set(payload, result)
    return result
