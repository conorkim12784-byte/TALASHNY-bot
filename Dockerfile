FROM nikolaik/python-nodejs:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# تثبيت bgutil server لتوليد po_token تلقائياً
RUN git clone --depth=1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /bgutil && \
    cd /bgutil/server && \
    npm install --ignore-scripts && \
    npx tsc

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir --upgrade --requirement requirements.txt
RUN pip3 install --no-cache-dir bgutil-ytdlp-pot-provider

CMD ["python3", "main.py"]
