import httpx
from app.reliability import retry_request
import json
from fastapi import HTTPException
class GeminiProvider():
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def _to_gemini(self, payload: dict) -> dict:
        contents = []
        system_text = None
        role_map = {"user": "user", "assistant": "model"}
        
        for msg in payload["messages"]:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_text = content
            else:
                contents.append({
                    "role": role_map[role],
                    "parts": [{"text": content}],
                })
        
        body = {"contents": contents}
        if system_text is not None:
            body["system_instruction"] = {"parts": [{"text": system_text}]}
        return  body
    
        
    async def chat(self, payload: dict) -> dict:
        model = payload.get("model") or self.model
        if not self.supports_model(model):
            model = self.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers={"x-goog-api-key": self.api_key}
        gemini_body = self._to_gemini(payload)

        async def do_request():
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, headers=headers, json=gemini_body)
                resp.raise_for_status()              # чтоб обёртка ловила 4xx/5xx
                data = resp.json()
                return self._to_openai(data, model)

        return await retry_request(do_request)
    
    async def chat_stream(self, payload: dict):
        model = payload.get("model") or self.model
        if not self.supports_model(model):
            model = self.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"
        headers = {"x-goog-api-key": self.api_key}
        gemini_body = self._to_gemini(payload)

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=gemini_body) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    chunk = json.loads(line[6:])

                    candidates = chunk.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        continue
                    text = parts[0]["text"]

                    out = {
                        "id": "gemini",
                        "object": "chat.completion.chunk",
                        "model": model,
                        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
                    }
                    yield f"data: {json.dumps(out, ensure_ascii=False)}\n\n".encode("utf-8")
        yield b"data: [DONE]\n\n"

    def _to_openai(self, data: dict, model: str) -> dict:
        candidates = data.get("candidates", [])
        if not candidates:
            raise HTTPException(status_code=502, detail=f"gemini returned no candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise HTTPException(status_code=502, detail=f"gemini returned no text: {data}")
        
        text = parts[0]["text"]
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)
        total_tokens = usage.get("totalTokenCount", 0)
        
        return {
            "model": model,
            "id": "gemini",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        }

    def supports_model(self, model: str) -> bool:
        return model.startswith("gemini")