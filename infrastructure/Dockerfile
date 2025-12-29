FROM python:3.13-slim

WORKDIR /echonotify

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN curl -o /usr/local/bin/wait-for-it.sh \
    https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

COPY requirements.txt ./
COPY pyproject.toml ./
COPY uv.lock ./

COPY README.md ./
COPY echonotify ./echonotify

RUN uv sync --frozen
COPY frontend ./frontend
COPY alembic.ini ./
COPY alembic ./alembic

COPY infrastructure/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
