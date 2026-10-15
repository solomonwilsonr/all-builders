"""Short-lived answers kept in memory (per instance), so the same link, listing or model number asked again within
minutes answers at once instead of re-reading pages and re-running models. Stored answers are copies: a caller
changing one never changes the cache."""
import copy
import threading
import time

_items: dict[str, tuple[float, object]] = {}
_lock = threading.Lock()
MAX_ITEMS = 500


def get(key: str):
    with _lock:
        hit = _items.get(key)
        if not hit:
            return None
        expires, value = hit
        if expires < time.monotonic():
            _items.pop(key, None)
            return None
        return copy.deepcopy(value)


def put(key: str, value, ttl_s: float) -> None:
    with _lock:
        if len(_items) >= MAX_ITEMS:  # drop the soonest to expire
            for k, _ in sorted(_items.items(), key=lambda kv: kv[1][0])[:MAX_ITEMS // 5]:
                _items.pop(k, None)
        _items[key] = (time.monotonic() + ttl_s, copy.deepcopy(value))


def clear() -> None:
    with _lock:
        _items.clear()
