#!/bin/bash
set -e

echo "Pulling latest code..."
git pull

echo "Building containers..."
docker compose -f docker-compose.prod.yml build

echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo "Running database migrations..."
docker compose exec api alembic upgrade head

echo "Deployment completed."
