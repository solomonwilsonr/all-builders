# Built from a staging folder that holds api/ and contracts/ side by side (see `make deploy-api`).
FROM python:3.12-slim
WORKDIR /srv
COPY api/pyproject.toml api/
RUN pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" "pyyaml>=6.0"
COPY api/app api/app
COPY contracts contracts
ENV CONTRACTS_DIR=/srv/contracts MOCK=1 PORT=8080
WORKDIR /srv/api
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
