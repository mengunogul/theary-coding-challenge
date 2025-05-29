#!/bin/sh

# Exit on any error
set -e

echo "Waiting for database to be ready..."

# Simple database readiness check using Django's check command
until uv run python manage.py check --database default; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run Django migrations
echo "Applying database migrations..."
uv run python manage.py migrate --noinput

echo "Starting Django server..."
exec uv run python -m uvicorn theary.asgi:application --host 0.0.0.0 --port 8000
