FROM python:3.10-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        curl \
        xz-utils \
        tor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# تثبيت Node.js 20 LTS مباشرة من المصدر الرسمي
RUN curl -fsSL https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz -o /tmp/node.tar.xz \
    && tar -xf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && node --version \
    && npm --version

COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

# تشغيل Tor قبل البوت
CMD tor --RunAsDaemon 1 --SocksPort 9050 && sleep 3 && python3 main.py
