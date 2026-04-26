# Dockerfile - بوت تليجرام لتحميل اليوتيوب + سيرفر PO Token
FROM python:3.11-slim

# أدوات النظام
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl ca-certificates gnupg \
 && rm -rf /var/lib/apt/lists/*

# تثبيت Node.js 20 (مطلوب لسيرفر bgutil POT)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# مكتبات بايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت سيرفر PO Token
RUN npm install -g bgutil-ytdlp-pot-provider

# كود البوت
COPY . .

# متغيرات البيئة
ENV POT_BASE_URL=http://127.0.0.1:4416
ENV PYTHONUNBUFFERED=1

# سكربت تشغيل: يبدأ سيرفر POT ثم ينتظر جاهزيته ثم يشغّل البوت
RUN printf '%s\n' \
'#!/bin/bash' \
'set -e' \
'echo "▶ تشغيل سيرفر POT..."' \
'bgutil-pot-server &' \
'POT_PID=$!' \
'echo "⏳ بانتظار جاهزية سيرفر POT على $POT_BASE_URL ..."' \
'for i in $(seq 1 30); do' \
'  if curl -sf "$POT_BASE_URL/ping" >/dev/null 2>&1 || curl -sf "$POT_BASE_URL" >/dev/null 2>&1; then' \
'    echo "✅ سيرفر POT جاهز"' \
'    break' \
'  fi' \
'  sleep 1' \
'done' \
'echo "🤖 تشغيل البوت..."' \
'exec python main.py' \
> /app/start.sh && chmod +x /app/start.sh

EXPOSE 4416
CMD ["/app/start.sh"]
