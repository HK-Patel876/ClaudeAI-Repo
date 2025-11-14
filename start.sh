#!/bin/bash

echo "🚀 Starting AI Trading System..."

# Start backend on port 8000
echo "📊 Starting FastAPI backend on port 8000..."
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend on port 5000
echo "🎨 Starting React frontend on port 5000..."
cd frontend && npm start &
FRONTEND_PID=$!

echo "✅ System started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Wait for both processes
wait
