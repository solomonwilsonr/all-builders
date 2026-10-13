# SafeShelf developer commands. Run from the repo root.
DATABASE_URL ?= postgresql://safeshelf:safeshelf@localhost:5442/safeshelf
# Passed to recipes through the environment, never as an argument, so the password stays out of `ps`.
export DATABASE_URL
GCP_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-south1
SQL_INSTANCE ?= $(GCP_PROJECT):$(REGION):safeshelf-db
DEPLOY_MOCK ?= 0

.PHONY: test-extension agents demo-pages api test db-up db-down load-data deploy-api bench

test-extension:  ## extension tests (plain Node, no Chrome, no network, no credits)
	node extension/tests/run_all.mjs

agents:         ## Shelf Chat agent service on :8081 (needs GOOGLE_API_KEY in .env or agents/.env)
	cd agents && uv run --python 3.12 uvicorn server:app --reload --port 8081

demo-pages:     ## serve the demo shop pages on :8090
	cd extension/demo && python3 -m http.server 8090

api:            ## run the API locally on :8080 (MOCK=1 by default)
	cd api && MOCK=$${MOCK:-1} PYTHONPATH=.. uv run --python 3.12 uvicorn app.main:app --reload --port 8080

test:           ## contract tests: every endpoint has a mock and is served
	cd api && uv run --python 3.12 pytest -q

db-up:          ## local Postgres + pgvector on :5442, tables from data/schema.sql
	docker compose up -d db

db-down:
	docker compose down

load-data:      ## CPSC recalls + Australian registry (TVs, fridges) into the local database
	uv run data/load_cpsc.py --from 2019 --to 2026 --summary
	uv run data/load_au_registry.py --types tv rf

deploy-api:     ## API to Cloud Run: real engine on Cloud SQL (DEPLOY_MOCK=1 for example answers only)
	rm -rf .build && mkdir -p .build && cp -R api engine contracts .build/ && mkdir -p .build/data && \
		cp data/bis_mock.json data/authorised_sellers.json data/demo_domains.json .build/data/ && \
		rm -rf .build/api/.venv .build/engine/.venv .build/engine/tests && cp api/Dockerfile .build/Dockerfile
	gcloud run deploy safeshelf-api --source .build --project $(GCP_PROJECT) --region $(REGION) \
		--allow-unauthenticated --min-instances 0 --memory 1Gi --timeout 300 \
		--add-cloudsql-instances $(SQL_INSTANCE) --set-secrets DB_PASSWORD=safeshelf-db-password:latest \
		--set-env-vars MOCK=$(DEPLOY_MOCK),CLOUD_SQL_INSTANCE=$(SQL_INSTANCE),GOOGLE_CLOUD_PROJECT=$(GCP_PROJECT)

bench:          ## M2 backtest: reviews from the bucket (once), Gemini labels (cached), bench/results.json + README
	@mkdir -p data/raw/amazon_reviews && gcloud storage cp --no-clobber \
		"gs://safeshelf-data-03d8d835/amazon_reviews_backtest/reviews_*.jsonl" data/raw/amazon_reviews/
	cd engine && PYTHONPATH=.. uv run --python 3.12 python ../bench/backtest.py
