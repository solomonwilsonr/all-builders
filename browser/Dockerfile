# A real Chrome (Chromium) with the SafeShelf extension, streamed with noVNC. See server.py.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium xvfb x11vnc xdotool novnc python3 python3-aiohttp python3-google-auth python3-requests \
      fonts-noto-core fonts-noto-cjk fonts-noto-color-emoji ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/safeshelf
COPY ext ./ext
COPY remote ./remote
# Pins the SafeShelf icon to the toolbar (the extension's ID is fixed by remote/extension-key.txt)
COPY remote/policy.json /etc/chromium/policies/managed/safeshelf.json
COPY server.py view.html ./
ENV PORT=8080 PYTHONUNBUFFERED=1
CMD ["python3", "/opt/safeshelf/server.py"]
