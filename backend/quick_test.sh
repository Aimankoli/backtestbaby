#!/bin/bash

###############################################################################
# Quick API Test - Fast testing for common scenarios
###############################################################################

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Quick API Test ===${NC}\n"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required. Install with: brew install jq${NC}"
    exit 1
fi

# Test 1: Health Check
echo -e "${BLUE}1. Testing health endpoint...${NC}"
response=$(curl -s "$BASE_URL/")
if echo "$response" | grep -q "BacktestMCP API"; then
    echo -e "${GREEN}✓ API is running${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    exit 1
fi

# Test 2: Register & Login
echo -e "\n${BLUE}2. Testing authentication...${NC}"
TIMESTAMP=$(date +%s)
RANDOM_NUM=$RANDOM
TEST_EMAIL="quicktest_${TIMESTAMP}_${RANDOM_NUM}@example.com"
TEST_PASSWORD="test123"

# Register (ignore errors if user exists)
curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"QuickTest_${TIMESTAMP}\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" > /dev/null 2>&1

# Login
response=$(curl -s -i -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

TOKEN=$(echo "$response" | grep -i "set-cookie: access_token=" | sed 's/.*access_token=\([^;]*\).*/\1/')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Authentication successful${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

# Test 3: Create Conversation
echo -e "\n${BLUE}3. Creating conversation...${NC}"
conv_response=$(curl -s -X POST "$BASE_URL/conversations/" \
    -H "Cookie: access_token=$TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"title":"Quick Test"}')

CONV_ID=$(echo "$conv_response" | jq -r '.id')

if [ -n "$CONV_ID" ] && [ "$CONV_ID" != "null" ]; then
    echo -e "${GREEN}✓ Conversation created: $CONV_ID${NC}"
else
    echo -e "${RED}✗ Failed to create conversation${NC}"
    exit 1
fi

# Test 4: Send Message with Backtest
echo -e "\n${BLUE}4. Testing backtest (this may take 30-60 seconds)...${NC}"
chat_response=$(curl -s -X POST "$BASE_URL/conversations/$CONV_ID/chat" \
    -H "Cookie: access_token=$TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"message":"Backtest a simple MA crossover on SPY from 2022-01-01 to 2023-01-01"}')

# Check if backtest executed
if echo "$chat_response" | grep -q "backtest_result"; then
    echo -e "${GREEN}✓ Backtest executed successfully${NC}"

    # Extract metrics
    metrics=$(echo "$chat_response" | grep "backtest_result" | jq '.data.metrics')
    echo -e "\n${BLUE}Metrics:${NC}"
    echo "$metrics" | jq '.'
else
    echo -e "${RED}✗ Backtest may have failed (check logs)${NC}"
fi

# Test 5: Verify Strategy
echo -e "\n${BLUE}5. Verifying strategy and files...${NC}"
sleep 2  # Wait for async saves

strategies=$(curl -s -X GET "$BASE_URL/strategies/" \
    -H "Cookie: access_token=$TOKEN")

STRAT_ID=$(echo "$strategies" | jq -r '.[0].id')

if [ -n "$STRAT_ID" ] && [ "$STRAT_ID" != "null" ]; then
    strategy=$(curl -s -X GET "$BASE_URL/strategies/$STRAT_ID" \
        -H "Cookie: access_token=$TOKEN")

    # Check for backtest code
    code=$(echo "$strategy" | jq -r '.backtest_code')
    if [ "$code" != "null" ] && [ -n "$code" ]; then
        code_len=$(echo "$code" | wc -c | tr -d ' ')
        echo -e "${GREEN}✓ Backtest code saved ($code_len bytes)${NC}"
    else
        echo -e "${RED}✗ Backtest code NOT saved${NC}"
    fi

    # Check for plot HTML
    plot_html=$(echo "$strategy" | jq -r '.backtest_results[0].plot_html')
    if [ "$plot_html" != "null" ] && [ -n "$plot_html" ]; then
        plot_len=$(echo "$plot_html" | wc -c | tr -d ' ')
        echo -e "${GREEN}✓ Plot HTML saved ($plot_len bytes) ✨${NC}"
    else
        echo -e "${RED}✗ Plot HTML NOT saved${NC}"
    fi

    # Check for data CSV
    data_csv=$(echo "$strategy" | jq -r '.backtest_results[0].data_csv')
    if [ "$data_csv" != "null" ] && [ -n "$data_csv" ]; then
        data_len=$(echo "$data_csv" | wc -c | tr -d ' ')
        echo -e "${GREEN}✓ Data CSV saved ($data_len bytes) ✨${NC}"
    else
        echo -e "${RED}✗ Data CSV NOT saved${NC}"
    fi
fi

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✨ Quick test completed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Conversation ID: $CONV_ID"
echo -e "Strategy ID: $STRAT_ID"
echo ""
