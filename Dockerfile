FROM nikolaik/python-nodejs:latest
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ntpdate \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt
CMD ["sh", "-c", "ntpdate -u time.google.com 2>/dev/null || true; python3 main.py"]
