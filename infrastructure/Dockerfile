FROM python:3.13-slim

WORKDIR /echonotify

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.0

RUN curl -o /usr/local/bin/wait-for-it.sh \
    https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it.sh

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-root

RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -d /home/appuser -m appuser

RUN mkdir -p /echonotify/logs /echonotify/static && \
    chown -R appuser:appgroup /echonotify

COPY --chown=appuser:appgroup echonotify ./echonotify
COPY --chown=appuser:appgroup frontend ./frontend
COPY --chown=appuser:appgroup alembic.ini ./
COPY --chown=appuser:appgroup alembic ./alembic

COPY infrastructure/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV PATH="/home/appuser/.local/bin:/echonotify/.venv/bin:${PATH}"
ENV PYTHONPATH="/echonotify:${PYTHONPATH}"

USER appuser

ENTRYPOINT ["sh", "/usr/local/bin/docker-entrypoint.sh"]

CMD ["uvicorn", "echonotify.main:app", "--host", "0.0.0.0", "--port", "8000"]
