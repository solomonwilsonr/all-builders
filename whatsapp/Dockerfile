FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
RUN pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" "httpx>=0.28" "google-genai>=1.0"
COPY bot.py app.py ./
ENV PORT=8080
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
