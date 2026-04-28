# ✅ نمط النسخة القديمة (World) — تشغيل بـ yt-dlp -g مباشر بدون cookies/POT
# الـ Dockerfile ده يشيل أي اعتمادات قديمة على bgutil-provider/POT server.

FROM nikolaik/python-nodejs:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt

CMD ["python3", "main.py"]
