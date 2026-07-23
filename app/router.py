
from fastapi import HTTPException


class Router:


    def __init__(self, providers: list):
        self.providers = providers


    async def chat(self, payload: dict) -> dict:
        last_error = None
        model = payload.get("model", "")
        preferred = [p for p in self.providers if p.supports_model(model)]
        others = [p for p in self.providers if not p.supports_model(model)]
        candidates = preferred + others
        for provider in candidates:
            try:
                result = await provider.chat(payload)
                if preferred and provider not in preferred:
                    print(f"[router] fallback: requested {model}, answered by {provider}")
                    result["fallback_from"] = model
                return result
            except Exception as e:
                last_error = e
        raise HTTPException(status_code=503, detail="all providers failed")

    async def chat_stream(self, payload: dict):
            last_error = None
            model = payload.get("model", "")
            preferred = [p for p in self.providers if p.supports_model(model)]
            others = [p for p in self.providers if not p.supports_model(model)]
            candidates = preferred + others

            for provider in candidates:
                try:
                    stream = provider.chat_stream(payload)   # генератор создан, но не запущен
                    first = await anext(stream)               # ← тут провайдер реально дёргается
                except Exception as e:
                    last_error = e
                    continue                                  # не завёлся — следующий
                yield first                                   # завёлся: отдаём первый кусок, потом остальное
                async for chunk in stream:
                    yield chunk
                return                                        # поток дошёл до конца — выходим
            error_chunk = f'data: {{"error": "all providers failed"}}\n\n'  # все провайдеры сдохли — отдаём ошибку куском (raise тут нельзя, поток уже начат)
            yield error_chunk.encode("utf-8")