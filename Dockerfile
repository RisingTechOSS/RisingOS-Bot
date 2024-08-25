FROM python:buster

WORKDIR /app
COPY . /app

RUN apt-get update && \
    apt-get install -y libcairo2 sshpass rsync && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --use-pep517 --no-cache-dir -r req.txt --break-system-packages

RUN chmod +x restart

ENTRYPOINT ["/bin/sh", "./restart"]
