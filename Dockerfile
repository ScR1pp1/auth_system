FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "sleep 5 && (alembic upgrade head || (echo 'Migrations are not applied, creating tables via create_tables' && python -c \"from app.database.database import create_tables; import asyncio; asyncio.run(create_tables())\")) && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]