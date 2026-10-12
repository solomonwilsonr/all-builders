# SafeShelf developer commands. Run from the repo root.
DATABASE_URL ?= postgresql://safeshelf:safeshelf@localhost:5442/safeshelf
# Passed to recipes through the environment, never as an argument, so the password stays out of `ps`.
export DATABASE_URL
GCP_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-south1

.PHONY: api test db-up db-down load-data deploy-api

api:            ## run the API locally on :8080 (MOCK=1 by default)
	cd api && MOCK=$${MOCK:-1} uv run --python 3.12 uvicorn app.main:app --reload --port 8080

test:           ## contract tests: every endpoint has a mock and is served
	cd api && uv run --python 3.12 pytest -q

db-up:          ## local Postgres + pgvector on :5442, tables from data/schema.sql
	docker compose up -d db

db-down:
	docker compose down

load-data:      ## CPSC recalls + Australian registry (TVs, fridges) into the local database
	uv run data/load_cpsc.py --from 2019 --to 2026 --summary
	uv run data/load_au_registry.py --types tv rf

deploy-api:     ## mock API to Cloud Run (needs gcloud login and a project)
	rm -rf .build && mkdir -p .build && cp -R api contracts .build/ && rm -rf .build/api/.venv && cp api/Dockerfile .build/Dockerfile
	gcloud run deploy safeshelf-api --source .build --project $(GCP_PROJECT) --region $(REGION) \
		--allow-unauthenticated --min-instances 0 --set-env-vars MOCK=1
