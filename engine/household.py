"""The household's products (the household inventory): what a household owns, with its warranty and return dates.

    add(tenant, owner, item)          a product the household owns; return_days / warranty_months become dates
    items(tenant, owner, search)      own products plus those of households shared with this owner
    due(rows, today)                  return windows and warranties that end within DUE_DAYS
    log_service(tenant, owner, id, entry)   a service request or warranty claim, kept on the product
    invite / accept / members / revoke      family sharing: the owner shares a code, the relative accepts it

Sharing needs both sides: the owner creates an invite, and only the person who accepts it can see the household's
products (read-only; they can't change or delete them). The owner can revoke it at any time. Owners are kept only as
hashes (engine/tenancy.py) and a receipt photo only as its SHA-256.
"""
import calendar
import secrets
from datetime import UTC, date, datetime, timedelta

from psycopg.types.json import Jsonb

from engine import store

DUE_DAYS = 14
INVITE_DAYS = 7
FIELDS = ("name", "brand", "model", "category", "product_id", "bought_from", "order_ref", "bought_on", "price",
          "currency", "return_by", "warranty_until", "receipt_sha256", "notes")


def _date(value) -> date | None:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


def add_months(start: date, months: int) -> date:
    month = start.month - 1 + months
    year, month = start.year + month // 12, month % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def dates(item: dict) -> dict:
    """bought_on + return_days -> return_by, bought_on + warranty_months -> warranty_until, unless given."""
    bought = _date(item.get("bought_on"))
    out = {"bought_on": bought, "return_by": _date(item.get("return_by")),
           "warranty_until": _date(item.get("warranty_until"))}
    if bought and not out["return_by"] and int(item.get("return_days") or 0) > 0:
        out["return_by"] = bought + timedelta(days=int(item["return_days"]))
    if bought and not out["warranty_until"] and int(item.get("warranty_months") or 0) > 0:
        out["warranty_until"] = add_months(bought, int(item["warranty_months"]))
    return out


def status(row: dict, today: date | None = None) -> dict:
    """Days left on the return window and the warranty; negative means it has ended."""
    today = today or datetime.now(UTC).date()
    left = {}
    for key, label in (("return_by", "return"), ("warranty_until", "warranty")):
        end = _date(row.get(key))
        if end:
            left[label] = {"until": end.isoformat(), "days_left": (end - today).days}
    return left


def due(rows: list[dict], today: date | None = None) -> list[dict]:
    """Return windows and warranties ending within DUE_DAYS (and not yet ended), soonest first."""
    soon = []
    for row in rows:
        for label, s in status(row, today).items():
            if 0 <= s["days_left"] <= DUE_DAYS:
                soon.append({"item_id": row.get("item_id"), "name": row.get("name"), "ends": label, **s})
    return sorted(soon, key=lambda d: d["days_left"])


def _need(owner_ref: str | None) -> str:
    if not owner_ref:
        raise ValueError("SafeShelf needs to know whose household this is: sign in (the screen sends X-Owner-Ref)")
    return owner_ref


def _out(row: dict, today: date | None = None) -> dict:
    row = dict(row)
    row["item_id"] = row.pop("id")
    for key in ("bought_on", "return_by", "warranty_until"):
        if row.get(key):
            row[key] = row[key].isoformat()
    if row.get("price") is not None:
        row["price"] = float(row["price"])
    row.pop("owner_ref", None)
    row.pop("tenant_id", None)
    row.pop("deleted_at", None)
    if row.get("created_at"):
        row["created_at"] = row["created_at"].isoformat()
    row["status"] = status(row, today)
    return row


def add(tenant_id: str, owner_ref: str | None, item: dict) -> dict:
    owner = _need(owner_ref)
    name = (item.get("name") or " ".join(v for v in (item.get("brand"), item.get("model")) if v)).strip()
    if not name:
        raise ValueError("give the product's name, or its brand and model")
    values = {k: item.get(k) for k in FIELDS} | dates(item) | {"name": name[:200]}
    item_id = store.short_id("HI-", tenant_id, owner, name, str(values.get("order_ref") or ""),
                             str(values.get("bought_on") or ""), secrets.token_hex(4))
    row = store.conn().execute(
        f"""INSERT INTO household_items (id, tenant_id, owner_ref, {", ".join(FIELDS)})
            VALUES (%s, %s, %s, {", ".join(["%s"] * len(FIELDS))}) RETURNING *""",
        (item_id, tenant_id, owner, *(values[k] for k in FIELDS))).fetchone()
    return _out(row)


def _shared_owners(tenant_id: str, owner_ref: str) -> list[str]:
    rows = store.conn().execute(
        """SELECT owner_ref FROM household_members WHERE tenant_id = %s AND member_ref = %s AND revoked_at IS NULL""",
        (tenant_id, owner_ref)).fetchall()
    return [r["owner_ref"] for r in rows]


def items(tenant_id: str, owner_ref: str | None, search: str | None = None) -> dict:
    owner = _need(owner_ref)
    shared = _shared_owners(tenant_id, owner)
    sql = """SELECT * FROM household_items WHERE tenant_id = %s AND owner_ref = ANY(%s) AND deleted_at IS NULL"""
    args: list = [tenant_id, [owner, *shared]]
    if search:
        sql += " AND (name ILIKE %s OR brand ILIKE %s OR model ILIKE %s OR category ILIKE %s)"
        args += [f"%{search.strip()}%"] * 4
    rows = store.conn().execute(sql + " ORDER BY created_at DESC LIMIT 200", args).fetchall()
    out = [_out(r) | {"shared": r["owner_ref"] != owner} for r in rows]
    return {"items": out, "due_soon": due(out), "shared_households": len(shared)}


def log_service(tenant_id: str, owner_ref: str | None, item_id: str, entry: dict) -> dict:
    """A service request, warranty claim or return on the owner's own product (members can't change it)."""
    owner = _need(owner_ref)
    record = {"opened_on": (_date(entry.get("opened_on")) or datetime.now(UTC).date()).isoformat(),
              **{k: str(entry[k])[:300] for k in ("kind", "status", "ref", "note") if entry.get(k)}}
    row = store.conn().execute(
        """UPDATE household_items SET service = service || %s::jsonb
           WHERE id = %s AND tenant_id = %s AND owner_ref = %s AND deleted_at IS NULL RETURNING *""",
        (Jsonb([record]), item_id, tenant_id, owner)).fetchone()
    if not row:
        raise KeyError(item_id)
    return _out(row)


def delete(tenant_id: str, owner_ref: str | None, item_id: str) -> dict:
    row = store.conn().execute(
        """UPDATE household_items SET deleted_at = now(), notes = NULL, order_ref = NULL, receipt_sha256 = NULL
           WHERE id = %s AND tenant_id = %s AND owner_ref = %s AND deleted_at IS NULL RETURNING id""",
        (item_id, tenant_id, _need(owner_ref))).fetchone()
    if not row:
        raise KeyError(item_id)
    return {"item_id": item_id, "deleted": True}


def invite(tenant_id: str, owner_ref: str | None) -> dict:
    owner = _need(owner_ref)
    code = "HS-" + secrets.token_hex(4).upper()
    store.conn().execute("INSERT INTO household_members (invite_code, tenant_id, owner_ref) VALUES (%s, %s, %s)",
                         (code, tenant_id, owner))
    return {"invite_code": code, "expires_in_days": INVITE_DAYS,
            "note": "Give this code only to the family member you want to share with. They type "
                    f"'join household {code}' in SafeShelf's chat within {INVITE_DAYS} days and can then see your "
                    "household's "
                    "products (not change them). You can stop sharing at any time."}


def accept(tenant_id: str, member_ref: str | None, code: str) -> dict:
    member = _need(member_ref)
    row = store.conn().execute(
        """UPDATE household_members SET member_ref = %s, accepted_at = now()
           WHERE invite_code = %s AND tenant_id = %s AND member_ref IS NULL AND revoked_at IS NULL
             AND owner_ref <> %s AND created_at > now() - make_interval(days => %s) RETURNING invite_code""",
        (member, (code or "").strip().upper(), tenant_id, member, INVITE_DAYS)).fetchone()
    if not row:
        raise ValueError("that invite code is wrong, already used or expired: ask for a new one")
    return {"joined": True, "invite_code": row["invite_code"],
            "note": "You can now see that household's products. Either of you can end the sharing."}


def members(tenant_id: str, owner_ref: str | None) -> dict:
    owner = _need(owner_ref)
    rows = store.conn().execute(
        """SELECT invite_code, accepted_at, owner_ref = %s AS mine FROM household_members
           WHERE tenant_id = %s AND (owner_ref = %s OR member_ref = %s) AND revoked_at IS NULL
             AND (accepted_at IS NOT NULL OR created_at > now() - make_interval(days => %s))""",
        (owner, tenant_id, owner, owner, INVITE_DAYS)).fetchall()
    return {"sharing": [{"invite_code": r["invite_code"], "accepted": r["accepted_at"] is not None,
                         "role": "you share your household" if r["mine"] else "shared with you"} for r in rows]}


def revoke(tenant_id: str, owner_ref: str | None, code: str) -> dict:
    """Either side ends the sharing: the owner revokes an invite, or the member leaves the household."""
    owner = _need(owner_ref)
    row = store.conn().execute(
        """UPDATE household_members SET revoked_at = now() WHERE invite_code = %s AND tenant_id = %s
           AND (owner_ref = %s OR member_ref = %s) AND revoked_at IS NULL RETURNING invite_code""",
        ((code or "").strip().upper(), tenant_id, owner, owner)).fetchone()
    if not row:
        raise KeyError(code)
    return {"invite_code": row["invite_code"], "revoked": True}
