#!/bin/bash

echo "🚀 Testing CosplayRadar Authentication System"
echo "============================================="

# Start Next.js server in background
cd /Users/lupodevelop/Git/GitHub/CosplayRadar/apps/web
npm run dev &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 8

# Test if server is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Server is running on http://localhost:3000"
else
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test registration API
echo "🧪 Testing registration API..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"testpassword123"}')

echo "Registration response: $REGISTER_RESPONSE"

# Test login API
echo "🧪 Testing login API..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpassword123"}')

echo "Login response: $LOGIN_RESPONSE"

# Clean up
echo "🧹 Cleaning up..."
kill $SERVER_PID 2>/dev/null

echo "✅ Test completed!"
echo ""
echo "🌐 To manually test:"
echo "   1. Run: cd apps/web && npm run dev"
echo "   2. Open: http://localhost:3000"
echo "   3. Try: Sign up / Sign in"
