#!/bin/bash

echo "🧪 Testing BankIQ+ Locally"
echo ""

# Check if backend is running
echo "1️⃣ Checking backend..."
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend not running. Start it with: cd backend && npm start"
    exit 1
fi

# Test agent invocation
echo ""
echo "2️⃣ Testing agent invocation..."
response=$(curl -s -X POST http://localhost:3001/api/invoke-agent \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Compare JPMorgan Chase vs Bank of America using ROE"}')

if echo "$response" | grep -q "output"; then
    echo "✅ Agent responding"
    echo "Response preview:"
    echo "$response" | python3 -m json.tool | head -20
else
    echo "❌ Agent not responding"
    echo "$response"
    exit 1
fi

echo ""
echo "3️⃣ Check frontend at http://localhost:3000"
echo ""
echo "✅ All systems operational!"
