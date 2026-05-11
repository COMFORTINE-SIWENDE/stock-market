#!/bin/bash

# Test script for new features: /auth/me endpoint and AI agent

BASE_URL="http://localhost:8000"

echo "=== Testing New Features ==="
echo ""

# Test 1: Register a new user
echo "1. Testing User Registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@test.com", "username": "newuser", "password": "test123", "full_name": "New User"}')
echo "$REGISTER_RESPONSE" | python3 -m json.tool
echo ""

# Test 2: Login
echo "2. Testing User Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "newuser", "password": "test123"}')
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)
echo ""

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token. Exiting."
  exit 1
fi

# Test 3: Get current user info (NEW ENDPOINT)
echo "3. Testing /auth/me endpoint (NEW)..."
curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Test 4: AI Agent Query (NEW FRONTEND PAGE)
echo "4. Testing AI Agent Query..."
echo "Query: 'What is the current price of AAPL?'"
curl -s -X POST "$BASE_URL/agent/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "What is the current price of AAPL?"}' | python3 -m json.tool
echo ""

echo "=== All Tests Complete ==="
echo ""
echo "✅ New Features:"
echo "  - /auth/me endpoint: Returns current user information"
echo "  - AI Agent page: frontend/pages/agent.html"
echo "  - Profile page: Now displays actual user info from API"
echo ""
echo "Access the AI Agent at: http://localhost:3000/pages/agent.html"
