#!/bin/bash

# Openclaw Bot Startup Script

set -e

echo "==================================="
echo "  Openclaw Bot - Startup Script"
echo "==================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "[INFO] Please edit .env file and configure your settings."
    echo "[INFO] At minimum, set TELEGRAM_BOT_TOKEN for the bot to work."
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check if a container is running
check_container() {
    docker ps --format '{{.Names}}' | grep -q "$1"
    return $?
}

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH"
    exit 1
fi

echo "[INFO] Starting Openclaw services..."

# Start only the essential services for testing (db + bot)
docker compose up -d db pgadmin

echo "[INFO] Waiting for database to be ready..."
sleep 5

# Check if database is healthy
if check_container "openclaw_db"; then
    echo "[OK] Database container is running"
else
    echo "[ERROR] Database container failed to start"
    exit 1
fi

# Start bot (optional - will fail gracefully if no Telegram token)
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "[INFO] Starting Telegram Bot..."
    docker compose up -d bot
    echo "[OK] Bot service started"
else
    echo "[WARNING] TELEGRAM_BOT_TOKEN not set. Skipping bot service."
fi

# Start API (optional)
echo "[INFO] Starting API service..."
docker compose up -d api
echo "[OK] API service started"

echo ""
echo "==================================="
echo "  Services Status"
echo "==================================="
docker compose ps

echo ""
echo "Access points:"
echo "  - API:       http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - pgAdmin:   http://localhost:5050"
echo "               (login: admin@openclaw.com / admin)"
echo ""
echo "To view logs:"
echo "  docker compose logs -f bot"
echo "  docker compose logs -f api"
echo ""
echo "To stop all services:"
echo "  docker compose down"
echo "==================================="
