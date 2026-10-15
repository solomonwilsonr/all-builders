# Built from a staging folder holding research/ and engine/ (only the shared click rules); see `make deploy-research`.
FROM python:3.12-slim
WORKDIR /srv
COPY research/requirements.txt research/
RUN pip install --no-cache-dir -r research/requirements.txt && playwright install --with-deps chromium
COPY engine engine
COPY research research
ENV PYTHONPATH=/srv:/srv/research PORT=8080
WORKDIR /srv/research
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
