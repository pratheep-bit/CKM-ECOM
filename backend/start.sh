#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application with Gunicorn..."
exec gunicorn app.main:app -c gunicorn.conf.py
