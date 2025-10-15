#!/bin/bash

echo "🚀 Starting Frontend..."
echo ""

cd frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "✅ Starting React app on port 3000..."
echo ""
echo "Backend is already running on port 3001"
echo ""
npm start
