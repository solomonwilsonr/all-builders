# Built from a staging folder holding research/ and engine/ (only the shared click rules); see `make deploy-research`.
FROM python:3.12-slim
WORKDIR /srv
COPY research/requirements.txt research/
RUN pip install --no-cache-dir -r research/requirements.txt && playwright install --with-deps chromium
# browser-use (open-source browser agent, MIT) in its own environment: it pins an older google-genai than the
# Research Agent uses. research/bu_runner.py runs there (research/browser_use_agent.py starts it).
RUN python -m venv /opt/bu && /opt/bu/bin/pip install --no-cache-dir "browser-use==0.13.11"
COPY engine engine
COPY research research
ENV PYTHONPATH=/srv:/srv/research PORT=8080
WORKDIR /srv/research
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
