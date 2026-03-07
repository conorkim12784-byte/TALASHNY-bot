FROM nikolaik/python-nodejs:python3.8-nodejs18

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ntpdate \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt

RUN python3 patch_session.py

CMD ["sh", "-c", "ntpdate -u time.google.com 2>/dev/null || true; python3 main.py"]
