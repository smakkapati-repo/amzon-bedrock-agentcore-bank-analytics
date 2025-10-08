#!/bin/bash

echo "🚀 Starting BankIQ+ Application..."

# Start backend
echo "Starting Flask backend..."
cd backend && python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend  
echo "Starting React frontend..."
cd ../frontend && npm start &
FRONTEND_PID=$!

echo "✅ BankIQ+ is running!"
echo "📊 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait