import hashlib, json, redis.asyncio as aioredis


class RedisCache:
    def __init__(self, url: str, ttl_seconds: int = 1800, fallback_ttl_seconds: int = 300):
        self._redis = aioredis.from_url(url, decode_responses=True)
        self.ttl = ttl_seconds
        self.fallback_ttl = fallback_ttl_seconds

    def _make_key(self, payload: dict) -> str:
        needed_keys = ["model", "messages", "temperature", "max_tokens"]
        new_dict = {key: payload[key] for key in needed_keys if key in payload}
        json_str = json.dumps(new_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    async def get(self, payload: dict):
        key = self._make_key(payload)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    
    async def set(self, payload: dict, response: dict) -> None:
        key = self._make_key(payload)
        ttl = self.fallback_ttl if "fallback_from" in response else self.ttl
        await self._redis.set(key, json.dumps(response, ensure_ascii=False), ex=ttl)