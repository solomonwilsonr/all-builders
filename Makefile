# SafeShelf developer commands. Run from the repo root.
DATABASE_URL ?= postgresql://safeshelf:safeshelf@localhost:5442/safeshelf
# Passed to recipes through the environment, never as an argument, so the password stays out of `ps`.
export DATABASE_URL
comma := ,
GCP_PROJECT ?= $(shell gcloud config get-value project 2>/dev/null)
REGION ?= asia-south1
SQL_INSTANCE ?= $(GCP_PROJECT):$(REGION):safeshelf-db
DEPLOY_MOCK ?= 0

API_URL ?= https://safeshelf-api-368488022657.asia-south1.run.app
# The Research Agent service (make deploy-research); empty = the API answers research requests with 503.
RESEARCH_URL ?= $(shell gcloud run services describe safeshelf-research --project $(GCP_PROJECT) --region $(REGION) --format 'value(status.url)' 2>/dev/null)
# The token the hourly re-check job sends (secret recheck-token, made by `make schedule-recheck`); empty until then.
RECHECK_SECRET ?= $(shell gcloud secrets describe recheck-token --project $(GCP_PROJECT) --format 'value(name)' 2>/dev/null)

.PHONY: test-extension agents demo-pages api test db-up db-down load-data deploy-api deploy-research schedule-recheck bench warm eval-agents web web-samples deploy-web

web:            ## the judges' page on :8095 (calls the live API)
	cd web && python3 -m http.server 8095

web-samples:    ## re-record the judges' page samples from the live API (after deploy-api)
	API_URL=$(API_URL) python3 web/record_samples.py

deploy-web:     ## the judges' page to Firebase Hosting, with the latest bench results
	cp bench/results.json web/data/bench.json && cp bench/agent_eval_results.json web/data/agent_eval.json && \
		cp bench/catalog_results.json web/data/catalog.json
	cd web && firebase deploy --only hosting --project $(GCP_PROJECT)

test-extension:  ## extension tests (plain Node, no Chrome, no network, no credits)
	node extension/tests/run_all.mjs

agents:         ## Shelf Chat agent service on :8081 (needs GOOGLE_API_KEY in .env or agents/.env)
	cd agents && uv run --python 3.12 uvicorn server:app --reload --port 8081

demo-pages:     ## serve the demo shop pages on :8090 (chat test console: http://localhost:8090/chat.html)
	cd extension/demo && python3 -m http.server 8090

api:            ## run the API locally on :8080 (MOCK=1 by default)
	cd api && MOCK=$${MOCK:-1} PYTHONPATH=.. uv run --python 3.12 uvicorn app.main:app --reload --port 8080

test:           ## contract tests: every endpoint has a mock and is served
	cd api && uv run --python 3.12 pytest -q

db-up:          ## local Postgres + pgvector on :5442, tables from data/schema.sql
	docker compose up -d db

db-down:
	docker compose down

load-data:      ## CPSC + JAPAC recalls (OECD GlobalRecalls) + India (CCPA, BIS) + Australian registry (TVs, fridges) into the local database
	uv run data/load_cpsc.py --from 2019 --to 2026 --summary
	uv run data/load_globalrecalls.py --from 2019 --summary
	cd engine && PYTHONPATH=.. uv run python ../data/load_india_notices.py --summary
	uv run data/load_au_registry.py --types tv rf

deploy-api:     ## API to Cloud Run: real engine on Cloud SQL (DEPLOY_MOCK=1 for example answers only)
	rm -rf .build && mkdir -p .build && cp -R api engine contracts .build/ && mkdir -p .build/data && \
		cp data/bis_mock.json data/authorised_sellers.json data/demo_domains.json .build/data/ && \
		mkdir -p .build/bench && cp bench/results.json .build/bench/ && \
		rm -rf .build/api/.venv .build/engine/.venv .build/engine/tests && cp api/Dockerfile .build/Dockerfile
	gcloud run deploy safeshelf-api --source .build --project $(GCP_PROJECT) --region $(REGION) \
		--allow-unauthenticated --min-instances 1 --max-instances 3 --memory 2Gi --timeout 300 \
		--add-cloudsql-instances $(SQL_INSTANCE) \
		--set-secrets DB_PASSWORD=safeshelf-db-password:latest$(if $(RESEARCH_URL),$(comma)SAFESHELF_RESEARCH_TOKEN=research-token:latest)$(if $(RECHECK_SECRET),$(comma)SAFESHELF_RECHECK_TOKEN=recheck-token:latest) \
		--set-env-vars MOCK=$(DEPLOY_MOCK),CLOUD_SQL_INSTANCE=$(SQL_INSTANCE),GOOGLE_CLOUD_PROJECT=$(GCP_PROJECT),SAFESHELF_PUBLIC_URL=$(API_URL)$(if $(RESEARCH_URL),$(comma)SAFESHELF_RESEARCH_URL=$(RESEARCH_URL))

schedule-recheck: ## every 30 min: recall sites searched again for one saved first-look model (then run make deploy-api)
	@gcloud secrets describe recheck-token --project $(GCP_PROJECT) >/dev/null 2>&1 || \
		openssl rand -hex 24 | tr -d '\n' | gcloud secrets create recheck-token --project $(GCP_PROJECT) --data-file=-
	@sa=$$(gcloud run services describe safeshelf-api --project $(GCP_PROJECT) --region $(REGION) --format 'value(spec.template.spec.serviceAccountName)'); \
		sa=$${sa:-$$(gcloud projects describe $(GCP_PROJECT) --format 'value(projectNumber)')-compute@developer.gserviceaccount.com}; \
		gcloud secrets add-iam-policy-binding recheck-token --project $(GCP_PROJECT) --member serviceAccount:$$sa \
			--role roles/secretmanager.secretAccessor >/dev/null
	@gcloud services enable cloudscheduler.googleapis.com --project $(GCP_PROJECT)
	@body=$$(mktemp); printf '{"mode":"recheck","limit":1,"token":"%s"}' \
		"$$(gcloud secrets versions access latest --secret recheck-token --project $(GCP_PROJECT))" > $$body; \
		verb=create; gcloud scheduler jobs describe safeshelf-recheck --project $(GCP_PROJECT) --location $(REGION) >/dev/null 2>&1 && verb=update; \
		gcloud scheduler jobs $$verb http safeshelf-recheck --project $(GCP_PROJECT) --location $(REGION) --schedule '*/30 * * * *' \
			--uri $(API_URL)/v1/agent/sessions --http-method POST --headers Content-Type=application/json \
			--attempt-deadline 300s --message-body-from-file $$body; status=$$?; rm -f $$body; exit $$status
	@echo "Scheduled. Now run: make deploy-api (it passes the token to the API)"

deploy-research: ## M9 Research Agent (headless Chromium) to Cloud Run; needs secret research-token (the API sends it)
	@gcloud secrets describe research-token --project $(GCP_PROJECT) >/dev/null 2>&1 || { echo "missing secret research-token"; exit 1; }
	rm -rf .build-research && mkdir -p .build-research/engine/agents && cp -R research .build-research/ && \
		cp engine/__init__.py engine/chat_core.py .build-research/engine/ && \
		cp engine/agents/__init__.py engine/agents/guard.py .build-research/engine/agents/ && \
		cp research/Dockerfile .build-research/Dockerfile
	gcloud run deploy safeshelf-research --source .build-research --project $(GCP_PROJECT) --region $(REGION) \
		--allow-unauthenticated --min-instances 0 --max-instances 2 --memory 2Gi --cpu 2 --timeout 300 \
		--concurrency 2 --set-secrets RESEARCH_TOKEN=research-token:latest \
		--set-env-vars GOOGLE_CLOUD_PROJECT=$(GCP_PROJECT)

deploy-whatsapp: ## M12 bot to Cloud Run; needs secrets wa-token, wa-phone-id, wa-app-secret, wa-verify-token
	@for s in wa-token wa-phone-id wa-app-secret wa-verify-token; do \
		gcloud secrets describe $$s --project $(GCP_PROJECT) >/dev/null 2>&1 || { echo "missing secret $$s (see whatsapp/README.md)"; exit 1; }; done
	gcloud run deploy safeshelf-whatsapp --source whatsapp --project $(GCP_PROJECT) --region $(REGION) \
		--allow-unauthenticated --min-instances 0 --memory 512Mi --timeout 300 --no-cpu-throttling \
		--set-secrets WA_TOKEN=wa-token:latest,WA_PHONE_ID=wa-phone-id:latest,WA_APP_SECRET=wa-app-secret:latest,WA_VERIFY_TOKEN=wa-verify-token:latest \
		--set-env-vars GOOGLE_CLOUD_PROJECT=$(GCP_PROJECT),SAFESHELF_API_URL=https://safeshelf-api-368488022657.asia-south1.run.app

bench:          ## M2 backtest: reviews from the bucket (once), Gemini labels (cached), bench/results.json + README
	@mkdir -p data/raw/amazon_reviews && gcloud storage cp --no-clobber \
		"gs://safeshelf-data-03d8d835/amazon_reviews_backtest/reviews_*.jsonl" data/raw/amazon_reviews/
	cd engine && PYTHONPATH=.. uv run --python 3.12 python ../bench/backtest.py

eval-agents:    ## agent test set (JAPAC cases with known answers) against API_URL; writes bench/agent_eval_results.json
	API_URL=$(API_URL) engine/.venv/bin/python bench/agent_eval.py

warm:           ## before a demo or recording: run every demo check once so the first click answers in seconds
	@for body in \
		'{"url":"https://demo.safeshelf.app/product/cx-65","title":"Kelvo CX-65 65W Dual-Port USB-C Fast Charger","price":1399,"currency":"INR","seller":"Kelvo Official Store"}' \
		'{"url":"https://example-deals-store.test/65w-charger","title":"65W Super Fast Charger - Kelvo CX-65 Original","price":299,"currency":"INR","page_text":"Brand Kelvo\nModel CX-65"}'; do \
		curl -s -o /dev/null -w "trust-check %{http_code} %{time_total}s\n" -X POST $(API_URL)/v1/listings/trust-check -H 'content-type: application/json' -d "$$body"; done
	@for p in SS-P-10291 SS-P-30118 SS-P-50001 SS-P-60002; do \
		curl -s -o /dev/null -w "safety $$p %{http_code} %{time_total}s\n" $(API_URL)/v1/products/$$p/safety; \
		curl -s -o /dev/null -w "certifications $$p %{http_code} %{time_total}s\n" $(API_URL)/v1/products/$$p/certifications; done
	@for p in SS-P-10291 SS-P-AMZ-B0BSKMH9GX; do \
		curl -s -o /dev/null -w "owner-guidance $$p %{http_code} %{time_total}s\n" $(API_URL)/v1/products/$$p/owner-guidance; done
