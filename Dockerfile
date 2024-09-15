FROM python:3.12-slim-bookworm

# Install Firefox dependencies. Needed for selenium
RUN apt update -y \
    && apt install --no-install-recommends --no-install-suggests -y \
    tzdata ca-certificates bzip2 curl wget libc-dev libxt6 \
    && apt install --no-install-recommends --no-install-suggests -y  \
    `apt-cache depends firefox-esr | awk '/Depends:/{print$2}'` \
    && update-ca-certificates

# Install nmap (required for host availability check)
RUN apt install nmap -y

# Cleanup unnecessary stuff
RUN apt purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && rm -rf /var/lib/apt/lists/* /tmp/*

ENV VENV_PATH=/opt/venv
RUN python3 -m venv "$VENV_PATH"
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
COPY feeds feeds
COPY check_my_feeds.py .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app"

CMD ["python3", "check_my_feeds.py"]