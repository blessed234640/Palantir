from fastapi import FastAPI
from app.schemas import ChatCompletionRequest
from app.providers.ollama import OllamaProvider
from fastapi.responses import StreamingResponse
from app.providers.gemini import GeminiProvider
from app.config import settings
from app.router import Router


app = FastAPI(title="шлюз")
provider = OllamaProvider(base_url="http://localhost:11434")
gemini = GeminiProvider(api_key=settings.gemini_api_key)
router = Router(providers=[provider, gemini])


@app.post("/v1/chat/completions")

async def chat_completions(request: ChatCompletionRequest):
    payload = request.model_dump()
    if request.stream:
        return StreamingResponse(provider.chat_stream(payload), media_type="text/event-stream")
    return await router.chat(payload)