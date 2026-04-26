FROM nikolaik/python-nodejs:latest

ENV PYTHONUNBUFFERED=1
ENV POT_BASE_URL=http://127.0.0.1:4416

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# PO Token server الخاص بـ yt-dlp — بدون cookies
RUN git clone --depth=1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /bgutil \
    && cd /bgutil/server \
    && npm install --ignore-scripts \
    && npx tsc

COPY . /app/
WORKDIR /app/

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir --upgrade --requirement requirements.txt

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'node /bgutil/server/build/main.js &' \
    'i=0' \
    'ready=0' \
    'while [ "$i" -lt 60 ]; do' \
    '  if curl -sf "$POT_BASE_URL/ping" >/dev/null 2>&1; then ready=1; break; fi' \
    '  i=$((i + 1))' \
    '  sleep 1' \
    'done' \
    'if [ "$ready" != "1" ]; then echo "POT server failed to start"; exit 1; fi' \
    'echo "POT server ready"' \
    'python3 -m yt_dlp --version' \
    'exec python3 main.py' \
    > /usr/local/bin/start-bot \
    && chmod +x /usr/local/bin/start-bot

CMD ["/usr/local/bin/start-bot"]
