"""The chat's memory of one conversation: which product it is about, the last turns, and an attached manual.

    load(session_id, owner) -> {product_id, link, market, history, document}   ({} when nothing is kept)
    save(session_id, owner, memory)

Screens used to send the whole history and the manual with every question; now a follow-up ("why?", "and the
warranty?", "what does E9 mean?") works from any screen and any API instance, WhatsApp included. Memory is kept only
for a known owner (the hashed X-Owner-Ref), so a session id alone never opens someone else's conversation. Rows older
than MAX_AGE_H are ignored. Best effort: if the database is down the chat answers without memory.
"""
import logging

from psycopg.types.json import Jsonb

from engine import store

log = logging.getLogger(__name__)
MAX_AGE_H = 24
MAX_TURNS = 12


def load(session_id: str | None, owner_ref: str | None) -> dict:
    if not (session_id and owner_ref):
        return {}
    try:
        row = store.conn().execute(
            """SELECT data, document FROM chat_memory WHERE session_id = %s AND owner_ref = %s
               AND updated_at > now() - make_interval(hours => %s)""", (session_id, owner_ref, MAX_AGE_H)).fetchone()
    except Exception as error:  # noqa: BLE001  no memory: the chat still answers
        log.info("chat memory not read: %s", type(error).__name__)
        return {}
    return {**(row["data"] or {}), **({"document": row["document"]} if row["document"] else {})} if row else {}


def remember(memory: dict, question: str, answer: str, **facts) -> dict:
    """The memory after one more turn: the turn added (the last MAX_TURNS kept) and the facts updated."""
    history = [*(memory.get("history") or []), {"role": "user", "text": question[:500]},
               {"role": "assistant", "text": answer[:800]}][-MAX_TURNS:]
    return {**memory, **{k: v for k, v in facts.items() if v is not None}, "history": history}


def save(session_id: str | None, owner_ref: str | None, memory: dict) -> None:
    if not (session_id and owner_ref):
        return
    data = {k: v for k, v in memory.items() if k != "document"}
    try:
        store.conn().execute(
            """INSERT INTO chat_memory (session_id, owner_ref, data, document) VALUES (%s, %s, %s, %s)
               ON CONFLICT (session_id, owner_ref) DO UPDATE SET data = EXCLUDED.data,
                 document = EXCLUDED.document, updated_at = now()""",
            (session_id, owner_ref, Jsonb(data), memory.get("document")))
    except Exception as error:  # noqa: BLE001
        log.info("chat memory not saved: %s", type(error).__name__)
