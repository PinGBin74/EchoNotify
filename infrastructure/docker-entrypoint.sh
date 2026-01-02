#!/bin/sh
set -e

if ! id -u appuser > /dev/null 2>&1; then
    groupadd -g 1000 appgroup 2>/dev/null || true
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser 2>/dev/null || true
fi

if [ -n "$WAIT_FOR_POSTGRES" ] && [ "$WAIT_FOR_POSTGRES" = "true" ]; then
    echo "Waiting for PostgreSQL..."
    /usr/local/bin/wait-for-it.sh postgres:5432 --timeout=30 -- echo "PostgreSQL is ready"
fi

if [ -n "$WAIT_FOR_REDIS" ] && [ "$WAIT_FOR_REDIS" = "true" ]; then
    echo "Waiting for Redis..."
    /usr/local/bin/wait-for-it.sh redis:6379 --timeout=30 -- echo "Redis is ready"
fi

if [ -n "$RUN_MIGRATIONS" ] && [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

exec "$@"
