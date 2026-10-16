"""Safety rules for talking to outside sources: a domain allowlist (also the SSRF guard), input sanitising, per-source
rate limits and circuit breakers. Adapters call these; nothing else in SafeShelf fetches an arbitrary URL.
"""
import ipaddress
import re
import socket
import threading
import time
from urllib.parse import urlparse

MAX_TERM = 80
# Letters in any script, digits, and the punctuation model numbers use. Everything else is dropped, so a query can't
# carry markup, wildcards or operators into a regulator's search.
TERM_CHARS = re.compile(r"[^\w\s\-./+#()&,'·・ー－／]", re.UNICODE)


def clean_term(text: str | None) -> str:
    text = TERM_CHARS.sub(" ", (text or "")[:MAX_TERM * 2])
    return re.sub(r"\s+", " ", text).strip()[:MAX_TERM]


def is_private_host(host: str) -> bool:
    """True for localhost, private, link-local and metadata addresses, given as an IP or resolving to one."""
    if not host or host.lower() in ("localhost", "metadata.google.internal", "metadata"):
        return True
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [ipaddress.ip_address(a[4][0]) for a in socket.getaddrinfo(host, None)]
        except (socket.gaierror, UnicodeError):
            return False  # unresolvable here; the fetch itself will fail
    return any(a.is_private or a.is_loopback or a.is_link_local or a.is_reserved or a.is_multicast
               for a in addresses)


def allowed_url(url: str, domains: list[str], resolve: bool = False) -> tuple[bool, str]:
    """May SafeShelf fetch (or cite as official) this URL for a source with these domains?"""
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("https", "http"):
        return False, "not a web address"
    if parsed.username or parsed.password:
        return False, "credentials in the address"
    try:
        ipaddress.ip_address(host)
        return False, "a bare IP address is never an official source"
    except ValueError:
        pass
    if not any(host == d or host.endswith("." + d) for d in domains):
        return False, f"{host or 'the address'} is not one of this source's official domains"
    if resolve and is_private_host(host):
        return False, "points at a private network address"
    return True, ""


def public_https_url(url: str) -> tuple[bool, str]:
    """For URLs a customer gives SafeShelf to call (webhooks): https, a public host, no credentials."""
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        return False, "must be https"
    if parsed.username or parsed.password:
        return False, "credentials in the address"
    if is_private_host(host):
        return False, "points at a private or internal address"
    return True, ""


class RateLimiter:
    """At most per_minute calls per source in any 60 s (in process; the API's shared limit is in engine.tenancy)."""

    def __init__(self):
        self.calls: dict[str, list[float]] = {}
        self.lock = threading.Lock()

    def allow(self, source_id: str, per_minute: int, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        with self.lock:
            window = [t for t in self.calls.get(source_id, []) if now - t < 60]
            if len(window) >= per_minute:
                self.calls[source_id] = window
                return False
            window.append(now)
            self.calls[source_id] = window
            return True


class CircuitBreaker:
    """After `threshold` failures in a row a source rests for `cooldown_s`; one trial call then decides."""

    def __init__(self, threshold: int = 3, cooldown_s: float = 300):
        self.threshold, self.cooldown_s = threshold, cooldown_s
        self.failures: dict[str, int] = {}
        self.opened_at: dict[str, float] = {}
        self.lock = threading.Lock()

    def allow(self, source_id: str, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        with self.lock:
            opened = self.opened_at.get(source_id)
            return opened is None or now - opened >= self.cooldown_s

    def record(self, source_id: str, ok: bool, now: float | None = None) -> None:
        now = now if now is not None else time.monotonic()
        with self.lock:
            if ok:
                self.failures[source_id] = 0
                self.opened_at.pop(source_id, None)
                return
            self.failures[source_id] = self.failures.get(source_id, 0) + 1
            if self.failures[source_id] >= self.threshold:
                self.opened_at[source_id] = now

    def state(self, source_id: str) -> str:
        return "open" if source_id in self.opened_at else "closed"


limiter = RateLimiter()
breaker = CircuitBreaker()
