import httpx
from fastapi import HTTPException
import asyncio 


async def retry_request(func, max_retries: int = 3):
    delay = 1
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return await func()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if 400 <= status_code < 500:
                raise                               # 4xx — не ретраим, пробрасываем
            last_error = e
        
        except httpx.RequestError as e:
            last_error = e
        # сюда попали = ретраебельная ошибка и не последняя попытка
        if attempt < max_retries:
            await asyncio.sleep(delay)
            delay *= 2
    raise last_error                               # попытки кончились — пробрасываем