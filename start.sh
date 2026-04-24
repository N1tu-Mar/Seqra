#!/bin/bash
set -e

echo "=== Seqra MVP ==="

# Backend
echo "[1/2] Starting Python backend on :8000..."
cd "$(dirname "$0")"
pip install -q -r requirements.txt
uvicorn python.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Frontend
echo "[2/2] Starting Svelte dev server on :5173..."
cd frontend
npm install --silent
npm run dev &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait
