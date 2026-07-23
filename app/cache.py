import hashlib, json, time


class InMemoryCache:
    def __init__(self, ttl_seconds: int = 1800, fallback_ttl_seconds: int = 300):
        self._store = {}                    # ключ → (ответ, время записи, ttl)
        self.ttl = ttl_seconds
        self.fallback_ttl = fallback_ttl_seconds

    def _make_key(self, payload: dict) -> str:

        needed_keys = ["model", "messages", "temperature", "max_tokens"]
        new_dict = {key: payload[key] for key in needed_keys if key in payload}
        json_str = json.dumps(new_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def get(self, payload: dict):
        key = self._make_key(payload)
        if key not in self._store:
            return None
        response, ts, ttl = self._store[key]
        if time.time() - ts > ttl:
            del self._store[key]
            return None
        return response

    def set(self, payload: dict, response: dict) -> None:
        key = self._make_key(payload)
        ttl = self.fallback_ttl if "fallback_from" in response else self.ttl
        self._store[key] = (response, time.time(), ttl)
