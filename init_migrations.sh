#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Checking database migrations..."
alembic current

if [ $? -ne 0 ]; then
    echo "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration"

    echo "Applying migrations..."
    alembic upgrade head
else
    echo "Migrations are already applied."
fi

echo "Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload