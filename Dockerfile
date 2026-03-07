FROM nikolaik/python-nodejs:python3.10-nodejs18

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ntpdate \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip3 install --no-cache-dir -U pip setuptools wheel
RUN pip3 install --no-cache-dir -r requirements.txt

CMD bash -c "ntpdate -u time.google.com || true && python3 main.py"
