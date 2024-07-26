FROM python:3.12-slim-bookworm

ENV VENV_PATH=/opt/venv
RUN python3 -m venv "$VENV_PATH"
ENV PATH="$VENV_PATH/bin:$PATH"

COPY requirements.txt .
COPY feeds .
COPY check_my_feeds.py .
RUN pip install -r --no-cache-dir requirements.txt

CMD ["python3", "check_my_feeds.py"]