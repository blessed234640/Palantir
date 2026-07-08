
from fastapi import HTTPException


class Router:


    def __init__(self, providers: list):
        self.providers = providers


    async def chat(self, payload: dict) -> dict:
        last_error = None
        for provider in self.providers:
            try:
                return await provider.chat(payload)
            except Exception as e:
                last_error = e        
        raise HTTPException(status_code=503, detail="all providers failed")
            