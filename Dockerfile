# Fixed: using Python 3.10 for pytgcalls compatibility
FROM nikolaik/python-nodejs:python3.10-nodejs18
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
COPY . /app/
WORKDIR /app/
RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --no-cache-dir -r requirements.txt
CMD ["python3", "main.py"]
