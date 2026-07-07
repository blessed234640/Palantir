import httpx
from fastapi import HTTPException
import asyncio 

class OllamaProvider():


    async def chat_stream(self, payload: dict):
        url = f"{self.base_url}/v1/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk


    def __init__(self, base_url: str):
        self.base_url = base_url
        

    async def chat(self, payload: dict) -> dict:
        url = f"{self.base_url}/v1/chat/completions"
        max_retries = 3
        delay = 1

        async with httpx.AsyncClient(timeout=60.0) as client:
            for attempt in range(1, max_retries + 1):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    return resp.json() # if mistake from group 200 we will leave at now, if not 200, maybe 500 group we go next
                
                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    
                    if 400 <= status_code < 500:
                        raise HTTPException(status_code=502, detail=f"upstream error: {e.response.text}")
                    # if mistake from 400 group, we fall at now, dont give retrie

                    if attempt == max_retries:
                        raise HTTPException(
                             status_code=502,
                             detail=f"upstream error: {e.response.text}"
                             )
                    
                    await asyncio.sleep(delay)
                    delay *= 2
                
                except httpx.RequestError:
                            if attempt == max_retries:
                                 raise HTTPException(
                                      status_code=503,
                                      detail="Ollama unavailable"
                                      )
                            await asyncio.sleep(delay)
                            delay *= 2