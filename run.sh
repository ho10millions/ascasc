#!/bin/bash
# Scrooge's Price Aggregator — simple run script
# Usage: ./run.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=== Scrooge's Price Aggregator ==="
echo ""

# 1. Start PostgreSQL if not running
if ! pg_isready -q 2>/dev/null; then
    echo "[1/4] Starting PostgreSQL..."
    service postgresql start 2>/dev/null || pg_ctlcluster 16 main start 2>/dev/null
else
    echo "[1/4] PostgreSQL already running"
fi

# 2. Create DB if needed
psql -U scrooge -d scrooge_db -c "SELECT 1" >/dev/null 2>&1 || {
    echo "       Creating database..."
    psql -U postgres -c "CREATE USER scrooge WITH PASSWORD 'scrooge_secret' SUPERUSER;" 2>/dev/null || true
    psql -U postgres -c "CREATE DATABASE scrooge_db OWNER scrooge;" 2>/dev/null || true
}

# 3. Start backend
echo "[2/4] Starting backend on :8000..."
cd "$BACKEND_DIR"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "       Backend PID: $BACKEND_PID"

# 4. Start frontend
echo "[3/4] Starting frontend on :3000..."
cd "$FRONTEND_DIR"
npx vite --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
echo "       Frontend PID: $FRONTEND_PID"

# 5. Start scraper worker (optional, in background)
echo "[4/4] Starting scraper worker..."
cd "$BACKEND_DIR"
python -m app.scrapers.worker &
WORKER_PID=$!
echo "       Worker PID: $WORKER_PID"

echo ""
echo "=== All services started ==="
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  First registration: use invite code SCROOGE-ADMIN-2024"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to kill all
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID $WORKER_PID 2>/dev/null; exit 0" INT TERM

# Wait for any process to exit
wait
