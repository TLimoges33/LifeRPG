#!/bin/bash
echo "🚀 Starting LifeRPG Full Stack Development Environment..."

# Start backend in background
echo "Starting backend..."
./scripts/start-backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "Starting frontend..."
./scripts/start-frontend.sh &
FRONTEND_PID=$!

echo "✅ LifeRPG Development Environment Started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
