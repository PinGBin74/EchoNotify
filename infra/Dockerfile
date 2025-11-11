FROM python:3.13-slim

WORKDIR /echonotify

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && python -m pip install --no-cache-dir uv \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY echonotify ./echonotify

RUN uv sync --frozen --no-dev

COPY . .

RUN apt-get update \
 && apt-get install -y --no-install-recommends wait-for-it \
 && rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", \
     "echo \"DATABASE_URL: $DATABASE_URL\"; \
      wait-for-it --host=$(echo $DATABASE_URL | sed 's/.*@\\([^:]*\\).*/\\1/') \
                  --port=5432 --timeout=30 -- \
      echo 'Database available'; \
      uv run alembic upgrade head; \
      uv run uvicorn echonotify.main:app --host 0.0.0.0 --port 8000 --reload"]