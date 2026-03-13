FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir --upgrade yt-dlp
CMD ["python3", "main.py"]
