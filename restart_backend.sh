#!/bin/bash
# restart_backend.sh - Restart the AI Video backend

echo "🔄 Restarting AiVideoForge Backend..."

# Find and kill any process on port 8000
echo "Checking for existing processes on port 8000..."
PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "Killing existing processes: $PIDS"
    echo "$PIDS" | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Verify port is free
if lsof -ti:8000 2>/dev/null | grep -q . ; then
    echo "⚠️  Port 8000 is still in use. Try: sudo lsof -ti:8000 | xargs kill -9"
    exit 1
fi

echo "✓ Port 8000 is free"

# Go to backend directory
cd /workspaces/ai-video/videoapp/backend

# Ensure dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt 2>&1 | tail -1

# Start backend
echo "Starting backend server on port 8000..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

