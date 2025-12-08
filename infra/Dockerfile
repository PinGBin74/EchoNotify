FROM python:3.12-slim

WORKDIR /echonotify

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -o /usr/local/bin/wait-for-it.sh \
    https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

COPY echonotify ./echonotify
COPY alembic.ini ./
COPY alembic ./alembic

CMD ["sh", "-c", "\
    /usr/local/bin/wait-for-it.sh postgres:5432 --timeout=30 -- echo 'Database is ready'; \
    alembic upgrade head; \
    exec uvicorn echonotify.main:app --host 0.0.0.0 --port 8000"]