@echo off
REM Openclaw Bot Startup Script for Windows

echo ===================================
echo   Openclaw Bot - Startup Script
echo ===================================

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [INFO] Please edit .env file and configure your settings.
    echo [INFO] At minimum, set TELEGRAM_BOT_TOKEN for the bot to work.
    goto :end
)

REM Load environment variables from .env
for /f "delims=" %%a in ('findstr /r /v "^#" .env ^| findstr /r /v "^$"') do (
    set "%%a"
)

echo [INFO] Starting Openclaw services...

REM Start only the essential services for testing (db + pgadmin)
docker compose up -d db pgadmin

echo [INFO] Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Check if database is running
docker ps --format "{{.Names}}" | findstr "openclaw_db" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Database container is running
) else (
    echo [ERROR] Database container failed to start
    goto :end
)

REM Start bot (optional - will fail gracefully if no Telegram token)
if defined TELEGRAM_BOT_TOKEN (
    echo [INFO] Starting Telegram Bot...
    docker compose up -d bot
    echo [OK] Bot service started
) else (
    echo [WARNING] TELEGRAM_BOT_TOKEN not set. Skipping bot service.
)

REM Start API (optional)
echo [INFO] Starting API service...
docker compose up -d api
echo [OK] API service started

echo.
echo ===================================
echo   Services Status
echo ===================================
docker compose ps

echo.
echo Access points:
echo   - API:       http://localhost:8000
echo   - API Docs:  http://localhost:8000/docs
echo   - pgAdmin:   http://localhost:5050
echo                (login: admin@openclaw.com / admin)
echo.
echo To view logs:
echo   docker compose logs -f bot
echo   docker compose logs -f api
echo.
echo To stop all services:
echo   docker compose down
echo ===================================

:end
