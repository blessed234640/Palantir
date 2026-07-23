import hashlib, json, time


class InMemoryCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._store = {}                    # ключ → (ответ, время записи)
        self.ttl = ttl_seconds

    def _make_key(self, payload: dict) -> str:

        needed_keys = ["model", "messages", "temperature", "max_tokens"]
        new_dict = {key: payload[key] for key in needed_keys if key in payload}
        json_str = json.dumps(new_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def get(self, payload: dict):
        key = self._make_key(payload)
        if key not in self._store:
            return None
        response, ts = self._store[key]
        if time.time() - ts > self.ttl:
            del self._store[key]
            return None
        return response

    def set(self, payload: dict, response: dict) -> None:
        key = self._make_key(payload)
        self._store[key] = (response, time.time())