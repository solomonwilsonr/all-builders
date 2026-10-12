# contracts/ (shared)

The agreement between Person A (Brain) and Person B (Face). **Change only after telling the other person.**

| File | What it is |
|---|---|
| `openapi.yaml` | Every API endpoint, its input and its answer. Each operation's `x-mock` names its example answer. |
| `mock/*.json` | One example answer per endpoint. The API returns these when `MOCK=1`, so Person B can build before the engine is ready. |
| `demo_products.json` | Fixed demo IDs used everywhere (all fictional). |

The database tables are in [`../data/schema.sql`](../data/schema.sql).

**Adding something new:** add the endpoint to `openapi.yaml` and an example to `mock/`, tell the other person, then build it. `make test` checks that every endpoint has a mock and that the mock API serves it.
