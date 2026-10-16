"""Signed webhooks for business tenants (plan v2.2 workstream I).

Each delivery is a POST of JSON with X-SafeShelf-Timestamp and X-SafeShelf-Signature: sha256=HMAC(secret,
"<timestamp>.<body>"). The per-webhook secret is derived from the server's key (SAFESHELF_WEBHOOK_KEY, from Secret
Manager) and the webhook id, shown once at creation, never stored (only its hash). The address must be public https,
and it is checked again at delivery time (a DNS change can't turn it into an internal address).
"""
import hashlib
import hmac
import json
import logging
import os
import threading
import time

import httpx

from engine import store
from engine.sources import policy

log = logging.getLogger(__name__)
EVENTS = ("investigation.complete", "watchlist.alert", "review.decided", "case.updated")
ATTEMPTS = 3


def _server_key() -> bytes:
    key = os.environ.get("SAFESHELF_WEBHOOK_KEY")
    if not key:
        raise RuntimeError("webhooks are not configured on this server (SAFESHELF_WEBHOOK_KEY)")
    return key.encode()


def secret_for(webhook_id: str) -> str:
    return "whsec_" + hmac.new(_server_key(), webhook_id.encode(), hashlib.sha256).hexdigest()


def sign(secret: str, timestamp: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()


def create(tenant_id: str, url: str, events: list[str]) -> dict:
    ok, why = policy.public_https_url(url)
    if not ok:
        raise ValueError(f"webhook address refused: {why}")
    bad = [e for e in events if e not in EVENTS]
    if bad or not events:
        raise ValueError(f"choose events from {EVENTS}")
    webhook_id = store.short_id("WH-", tenant_id, url, str(time.time_ns()))
    secret = secret_for(webhook_id)
    store.conn().execute(
        "INSERT INTO webhooks (id, tenant_id, url, secret_hash, events) VALUES (%s, %s, %s, %s, %s)",
        (webhook_id, tenant_id, url, hashlib.sha256(secret.encode()).hexdigest(), events))
    return {"webhook_id": webhook_id, "url": url, "events": events, "signing_secret": secret,
            "signature": "X-SafeShelf-Signature: sha256=HMAC_SHA256(signing_secret, '<X-SafeShelf-Timestamp>.<body>')",
            "note": "The signing secret is shown once."}


def _deliver(hook: dict, event: str, payload: dict) -> None:
    body = json.dumps({"event": event, "data": payload}, default=str, ensure_ascii=False).encode()
    status = None
    for attempt in range(1, ATTEMPTS + 1):
        ok, why = policy.public_https_url(hook["url"])
        if not ok:
            log.warning("webhook %s refused at delivery: %s", hook["id"], why)
            break
        stamp = str(int(time.time()))
        try:
            response = httpx.post(hook["url"], content=body, timeout=8, follow_redirects=False, headers={
                "content-type": "application/json", "X-SafeShelf-Event": event, "X-SafeShelf-Timestamp": stamp,
                "X-SafeShelf-Signature": sign(secret_for(hook["id"]), stamp, body)})
            status = response.status_code
            if status < 500:
                break
        except httpx.HTTPError:
            status = None
        time.sleep(2 ** attempt)
    store.conn().execute(
        "INSERT INTO webhook_deliveries (webhook_id, event, status, attempts, payload_hash) "
        "VALUES (%s, %s, %s, %s, %s)",
        (hook["id"], event, status, attempt, hashlib.sha256(body).hexdigest()))


def emit(tenant_id: str, event: str, payload: dict) -> int:
    """Deliver to this tenant's webhooks for the event, in the background. Returns how many will be called."""
    try:
        hooks = store.conn().execute(
            "SELECT id, url FROM webhooks WHERE tenant_id = %s AND %s = ANY(events) AND disabled_at IS NULL",
            (tenant_id, event)).fetchall()
        _server_key()
    except Exception as error:  # noqa: BLE001  no webhooks table or key: nothing to deliver
        log.debug("no webhooks: %s", type(error).__name__)
        return 0
    for hook in hooks:
        threading.Thread(target=_deliver, args=(hook, event, payload), daemon=True).start()
    return len(hooks)
