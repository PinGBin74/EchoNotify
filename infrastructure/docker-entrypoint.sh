
#!/bin/sh
set -e

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
