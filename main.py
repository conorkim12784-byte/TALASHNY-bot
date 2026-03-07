FROM nikolaik/python-nodejs:python3.10-nodejs18

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir -U pip setuptools wheel
RUN pip3 install --no-cache-dir \
    "pyrogram==2.0.106" \
    "TgCrypto" \
    "py-tgcalls==0.9.2" \
    "motor" \
    "pymongo" \
    "dnspython" \
    "python-dotenv" \
    "yt-dlp" \
    "aiohttp" \
    "aiofiles" \
    "Pillow" \
    "requests" \
    "psutil"

CMD ["python3", "main.py"]
