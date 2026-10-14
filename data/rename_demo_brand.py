"""One-off: rename the placeholder demo brand in an existing database (14 Oct 2026).

The demo charger was "ExampleBrand" with BIS number "R-41XXXXXX", which looked like placeholder data on screen.
It is now the (still fictional) "Kelvo", certificate "R-41097318", in the code and contracts. This updates rows
already stored, in one transaction, without re-running the seed (no Gemini calls, no duplicate rows).

    DATABASE_URL=... (Cloud SQL via cloud-sql-proxy) PYTHONPATH=.. uv run --python 3.12 python ../data/rename_demo_brand.py
"""
from engine import store

TABLES = ["products", "listings", "product_fingerprints", "certifications", "evidence", "investigation_steps"]
PAIRS = [("ExampleBrand", "Kelvo"), ("examplebrand", "kelvo"), ("EXAMPLEBRAND", "KELVO"), ("R-41XXXXXX", "R-41097318")]
OLD = ("%examplebrand%", "%R-41XXXXXX%")


def main() -> None:
    c = store.conn()
    with c.transaction():
        for table in TABLES:
            columns = c.execute(
                """SELECT column_name, udt_name FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = %s
                     AND udt_name IN ('text', 'varchar', 'json', 'jsonb', '_text')""", (table,)).fetchall()
            for col in columns:
                name, cast = col["column_name"], {"_text": "text[]"}.get(col["udt_name"], col["udt_name"])
                expr = f'"{name}"::text'
                for old, new in PAIRS:
                    expr = f"replace({expr}, '{old}', '{new}')"
                updated = c.execute(f'UPDATE "{table}" SET "{name}" = ({expr})::{cast} '
                                    f'WHERE "{name}"::text ILIKE %s OR "{name}"::text LIKE %s', OLD).rowcount
                if updated:
                    print(f"{table}.{name}: {updated} rows")
        left = sum(c.execute(f'SELECT count(*) AS n FROM "{t}" x WHERE x::text ILIKE %s OR x::text LIKE %s',
                             OLD).fetchone()["n"] for t in TABLES)
        if left:
            raise SystemExit(f"{left} rows still mention the old names; nothing was changed")
    print("done: no rows mention ExampleBrand or R-41XXXXXX")


if __name__ == "__main__":
    main()
