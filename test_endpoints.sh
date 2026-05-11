#!/bin/bash

# Stock Market Prediction System - Endpoint Testing Script
# This script tests all backend API endpoints

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Stock Market API Endpoint Tests"
echo "=========================================="
echo ""

# Test 1: Symbol Search
echo "1. Testing Symbol Search..."
RESPONSE=$(curl -s "$BASE_URL/symbols/search?q=AAPL")
if echo "$RESPONSE" | grep -q "AAPL"; then
    echo -e "${GREEN}✓ Symbol search working${NC}"
    echo "   Response: $RESPONSE"
else
    echo -e "${RED}✗ Symbol search failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 2: Stock Price
echo "2. Testing Stock Price..."
RESPONSE=$(curl -s "$BASE_URL/stocks/AAPL/price")
if echo "$RESPONSE" | grep -q "price"; then
    echo -e "${GREEN}✓ Stock price working${NC}"
    echo "   Response: $RESPONSE"
else
    echo -e "${RED}✗ Stock price failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 3: Historical Data
echo "3. Testing Historical Data..."
RESPONSE=$(curl -s "$BASE_URL/stocks/AAPL/data?start=2026-04-01&end=2026-05-11")
if echo "$RESPONSE" | grep -q "data"; then
    RECORD_COUNT=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['data']))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Historical data working${NC}"
    echo "   Records returned: $RECORD_COUNT"
else
    echo -e "${RED}✗ Historical data failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 4: Technical Indicators
echo "4. Testing Technical Indicators..."
RESPONSE=$(curl -s "$BASE_URL/stocks/AAPL/indicators?start=2026-04-01&end=2026-05-11")
if echo "$RESPONSE" | grep -q "indicators"; then
    echo -e "${GREEN}✓ Technical indicators working${NC}"
    echo "   Response: $RESPONSE"
else
    echo -e "${RED}✗ Technical indicators failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 5: Predictions
echo "5. Testing Predictions (5 days)..."
RESPONSE=$(curl -s "$BASE_URL/predictions/AAPL?days=5")
if echo "$RESPONSE" | grep -q "predictions"; then
    PRED_COUNT=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['predictions']))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Predictions working${NC}"
    echo "   Predictions returned: $PRED_COUNT"
    echo "   Sample: $(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); p=d['predictions'][0]; print(f\"{p['target_date']}: \${p['predicted_price']:.2f} ({p['trend_direction']})\")" 2>/dev/null || echo "N/A")"
else
    echo -e "${RED}✗ Predictions failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 6: Sentiment Analysis
echo "6. Testing Sentiment Analysis..."
RESPONSE=$(curl -s -X POST "$BASE_URL/sentiment/AAPL/analyze")
if echo "$RESPONSE" | grep -q "articles_analyzed"; then
    echo -e "${GREEN}✓ Sentiment analysis working${NC}"
    echo "   Response: $RESPONSE"
else
    echo -e "${RED}✗ Sentiment analysis failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 7: User Registration
echo "7. Testing User Registration..."
RANDOM_NUM=$RANDOM
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test${RANDOM_NUM}@example.com\",\"username\":\"testuser${RANDOM_NUM}\",\"password\":\"Test1234!\",\"full_name\":\"Test User\"}")
if echo "$RESPONSE" | grep -q "username"; then
    echo -e "${GREEN}✓ User registration working${NC}"
    echo "   Response: $RESPONSE"
    TEST_USERNAME="testuser${RANDOM_NUM}"
else
    echo -e "${YELLOW}⚠ User registration (might already exist)${NC}"
    echo "   Response: $RESPONSE"
    TEST_USERNAME="testuser123"
fi
echo ""

# Test 8: User Login
echo "8. Testing User Login..."
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username_or_email\":\"${TEST_USERNAME}\",\"password\":\"Test1234!\"}")
if echo "$RESPONSE" | grep -q "token"; then
    echo -e "${GREEN}✓ User login working${NC}"
    TOKEN=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])" 2>/dev/null)
    echo "   Token received: ${TOKEN:0:50}..."
else
    echo -e "${RED}✗ User login failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 9: Authenticated Logout (if we have a token)
if [ ! -z "$TOKEN" ]; then
    echo "9. Testing Get Current User (/auth/me)..."
    RESPONSE=$(curl -s -X GET "$BASE_URL/auth/me" \
      -H "Authorization: Bearer $TOKEN")
    if echo "$RESPONSE" | grep -q "username"; then
        echo -e "${GREEN}✓ Get current user working${NC}"
        USER_INFO=$(echo "$RESPONSE" | python3 -c "import json,sys; u=json.load(sys.stdin); print(f\"{u['username']} ({u['email']})\")" 2>/dev/null || echo "N/A")
        echo "   User: $USER_INFO"
    else
        echo -e "${RED}✗ Get current user failed${NC}"
        echo "   Response: $RESPONSE"
    fi
    echo ""
    
    echo "10. Testing Authenticated Logout..."
    RESPONSE=$(curl -s -X POST "$BASE_URL/auth/logout" \
      -H "Authorization: Bearer $TOKEN")
    if echo "$RESPONSE" | grep -q "Logged out"; then
        echo -e "${GREEN}✓ Logout working${NC}"
        echo "   Response: $RESPONSE"
    else
        echo -e "${RED}✗ Logout failed${NC}"
        echo "   Response: $RESPONSE"
    fi
    echo ""
fi

# Test 11: Prediction History
echo "11. Testing Prediction History..."
RESPONSE=$(curl -s "$BASE_URL/predictions/AAPL/history")
if echo "$RESPONSE" | grep -q "history"; then
    HISTORY_COUNT=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['history']))" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓ Prediction history working${NC}"
    echo "   History records: $HISTORY_COUNT"
else
    echo -e "${RED}✗ Prediction history failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 12: Agent Query
echo "12. Testing AI Agent Query..."
RESPONSE=$(curl -s -X POST "$BASE_URL/agent/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the current price of AAPL?"}')
if echo "$RESPONSE" | grep -q "response"; then
    echo -e "${GREEN}✓ AI Agent working${NC}"
    AGENT_RESPONSE=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['response'][:100])" 2>/dev/null || echo "N/A")
    echo "   Agent response: ${AGENT_RESPONSE}..."
else
    echo -e "${RED}✗ AI Agent failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

# Test 13: Data Collection (for TSLA as a new symbol)
echo "13. Testing Data Collection (TSLA)..."
RESPONSE=$(curl -s -X POST "$BASE_URL/stocks/collect" \
  -H "Content-Type: application/json" \
  -d '{"symbols":["TSLA"],"days":30}')
if echo "$RESPONSE" | grep -q "TSLA"; then
    echo -e "${GREEN}✓ Data collection working${NC}"
    echo "   Response: $RESPONSE"
else
    echo -e "${RED}✗ Data collection failed${NC}"
    echo "   Response: $RESPONSE"
fi
echo ""

echo "=========================================="
echo "Test Summary Complete"
echo "=========================================="
echo ""
echo "All 13 endpoints have been tested."
echo "Check the results above for any failures."
echo ""
