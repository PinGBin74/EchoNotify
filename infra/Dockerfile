FROM python:3.13-slim-bookworm

WORKDIR /echonotify

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY echonotify ./echonotify
COPY alembic.ini ./
COPY alembic ./alembic

RUN curl -sSL https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -o /usr/local/bin/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /echonotify
USER appuser

CMD ["sh", "-c", "\
    /usr/local/bin/wait-for-it.sh postgres:5432 --timeout=30 -- echo 'Database is ready'; \
    alembic upgrade head; \
    exec uvicorn echonotify.main:app --host 0.0.0.0 --port 8000"]