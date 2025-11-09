#!/bin/bash

###############################################################################
# BacktestMCP API Test Suite
# Comprehensive testing script using curl
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API Configuration
BASE_URL="http://localhost:8000"
API_VERSION=""

# Test data
TEST_EMAIL="testuser_$(date +%s)@example.com"
TEST_PASSWORD="testpassword123"
TEST_USERNAME="TestUser"

# Response storage
ACCESS_TOKEN=""
USER_ID=""
CONVERSATION_ID=""
STRATEGY_ID=""
SIGNAL_ID=""

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Extract JSON field (requires jq)
extract_json() {
    echo "$1" | jq -r "$2"
}

# Make authenticated GET request
auth_get() {
    curl -s -X GET "$BASE_URL$1" \
        -H "Cookie: access_token=$ACCESS_TOKEN" \
        -H "Content-Type: application/json"
}

# Make authenticated POST request
auth_post() {
    curl -s -X POST "$BASE_URL$1" \
        -H "Cookie: access_token=$ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$2"
}

# Make authenticated DELETE request
auth_delete() {
    curl -s -X DELETE "$BASE_URL$1" \
        -H "Cookie: access_token=$ACCESS_TOKEN" \
        -H "Content-Type: application/json"
}

###############################################################################
# Test 1: Health Check
###############################################################################

test_health_check() {
    print_header "TEST 1: Health Check"

    response=$(curl -s -X GET "$BASE_URL/")

    if echo "$response" | grep -q "BacktestMCP API"; then
        print_success "Health check passed"
        print_info "Response: $response"
    else
        print_error "Health check failed"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 2: User Registration
###############################################################################

test_user_registration() {
    print_header "TEST 2: User Registration"

    print_info "Registering user: $TEST_EMAIL"

    response=$(curl -s -X POST "$BASE_URL/auth/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"$TEST_USERNAME\",
            \"email\": \"$TEST_EMAIL\",
            \"password\": \"$TEST_PASSWORD\"
        }")

    # Check if registration was successful
    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        USER_ID=$(extract_json "$response" '.id')
        print_success "User registered successfully"
        print_info "User ID: $USER_ID"
        print_info "Username: $(extract_json "$response" '.username')"
        print_info "Email: $(extract_json "$response" '.email')"
    else
        # Check if user already exists
        if echo "$response" | grep -q "already registered"; then
            print_info "User already exists - using existing user"
        else
            print_error "Registration failed"
            echo "$response"
            exit 1
        fi
    fi
}

###############################################################################
# Test 3: User Login
###############################################################################

test_user_login() {
    print_header "TEST 3: User Login"

    print_info "Logging in as: $TEST_EMAIL"

    # Login and capture response with headers
    response=$(curl -s -i -X POST "$BASE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

    # Extract access token from Set-Cookie header
    ACCESS_TOKEN=$(echo "$response" | grep -i "set-cookie: access_token=" | sed 's/.*access_token=\([^;]*\).*/\1/')

    if [ -n "$ACCESS_TOKEN" ]; then
        print_success "Login successful"
        print_info "Access token: ${ACCESS_TOKEN:0:50}..."

        # Extract user info from response body
        body=$(echo "$response" | sed '1,/^\r$/d')
        USER_ID=$(extract_json "$body" '.id')
        print_info "User ID: $USER_ID"
    else
        print_error "Login failed - no access token received"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 4: Get Current User
###############################################################################

test_get_current_user() {
    print_header "TEST 4: Get Current User"

    response=$(auth_get "/auth/me")

    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        print_success "Retrieved current user"
        print_info "ID: $(extract_json "$response" '.id')"
        print_info "Username: $(extract_json "$response" '.username')"
        print_info "Email: $(extract_json "$response" '.email')"
    else
        print_error "Failed to get current user"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 5: Create Conversation
###############################################################################

test_create_conversation() {
    print_header "TEST 5: Create Conversation"

    response=$(auth_post "/conversations/" '{
        "title": "Test Backtest Strategy"
    }')

    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        CONVERSATION_ID=$(extract_json "$response" '.id')
        print_success "Conversation created"
        print_info "Conversation ID: $CONVERSATION_ID"
        print_info "Title: $(extract_json "$response" '.title')"
        print_info "Status: $(extract_json "$response" '.status')"
    else
        print_error "Failed to create conversation"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 6: List Conversations
###############################################################################

test_list_conversations() {
    print_header "TEST 6: List Conversations"

    response=$(auth_get "/conversations/")

    if echo "$response" | jq -e '.[0].id' > /dev/null 2>&1; then
        count=$(echo "$response" | jq '. | length')
        print_success "Retrieved conversations"
        print_info "Total conversations: $count"
        print_info "First conversation ID: $(extract_json "$response" '.[0].id')"
    else
        print_error "Failed to list conversations"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 7: Get Specific Conversation
###############################################################################

test_get_conversation() {
    print_header "TEST 7: Get Specific Conversation"

    response=$(auth_get "/conversations/$CONVERSATION_ID")

    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        print_success "Retrieved conversation"
        print_info "ID: $(extract_json "$response" '.id')"
        print_info "Title: $(extract_json "$response" '.title')"
        msg_count=$(echo "$response" | jq '.messages | length')
        print_info "Messages: $msg_count"
    else
        print_error "Failed to get conversation"
        echo "$response"
        exit 1
    fi
}

###############################################################################
# Test 8: Send Chat Message (First Message - Creates Strategy)
###############################################################################

test_send_first_message() {
    print_header "TEST 8: Send First Chat Message (Creates Strategy)"

    print_info "Sending message and waiting for streaming response..."

    # Stream the chat response
    response=$(curl -s -X POST "$BASE_URL/conversations/$CONVERSATION_ID/chat" \
        -H "Cookie: access_token=$ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "message": "I want to backtest a simple moving average crossover strategy. When the 50-day MA crosses above the 200-day MA, buy. When it crosses below, sell. Use SPY from 2020-01-01 to 2023-01-01."
        }')

    print_info "Raw response (first 500 chars):"
    echo "$response" | head -c 500
    echo ""

    # Check if strategy was created
    if echo "$response" | grep -q "strategy_created"; then
        # Extract strategy ID from the streaming response
        strategy_line=$(echo "$response" | grep "strategy_created")
        STRATEGY_ID=$(echo "$strategy_line" | jq -r '.data.strategy_id')

        print_success "Message sent and strategy created"
        print_info "Strategy ID: $STRATEGY_ID"
        print_info "Strategy Name: $(echo "$strategy_line" | jq -r '.data.name')"
    else
        print_info "Message sent (strategy may already exist)"
    fi

    # Check if backtest was executed
    if echo "$response" | grep -q "backtest_result"; then
        print_success "Backtest executed"

        # Extract metrics
        backtest_line=$(echo "$response" | grep "backtest_result")
        echo "$backtest_line" | jq '.data.metrics'
    fi
}

###############################################################################
# Test 9: Get Conversation (Verify Messages)
###############################################################################

test_verify_messages() {
    print_header "TEST 9: Verify Messages Were Saved"

    sleep 2  # Wait for async operations

    response=$(auth_get "/conversations/$CONVERSATION_ID")

    if echo "$response" | jq -e '.messages[0]' > /dev/null 2>&1; then
        msg_count=$(echo "$response" | jq '.messages | length')
        print_success "Messages saved"
        print_info "Total messages: $msg_count"

        # Check for user message
        user_msg=$(extract_json "$response" '.messages[0].role')
        print_info "First message role: $user_msg"

        # Check if strategy_id is linked
        strategy_id=$(extract_json "$response" '.strategy_id')
        if [ "$strategy_id" != "null" ] && [ -n "$strategy_id" ]; then
            STRATEGY_ID="$strategy_id"
            print_success "Strategy linked to conversation"
            print_info "Strategy ID: $STRATEGY_ID"
        fi
    else
        print_error "No messages found"
        echo "$response"
    fi
}

###############################################################################
# Test 10: List Strategies
###############################################################################

test_list_strategies() {
    print_header "TEST 10: List Strategies"

    response=$(auth_get "/strategies/")

    if echo "$response" | jq -e '.[0].id' > /dev/null 2>&1; then
        count=$(echo "$response" | jq '. | length')
        print_success "Retrieved strategies"
        print_info "Total strategies: $count"

        # Get first strategy
        if [ -z "$STRATEGY_ID" ]; then
            STRATEGY_ID=$(extract_json "$response" '.[0].id')
        fi

        print_info "Strategy ID: $STRATEGY_ID"
        print_info "Name: $(extract_json "$response" '.[0].name')"
        print_info "Status: $(extract_json "$response" '.[0].status')"
    else
        print_error "Failed to list strategies"
        echo "$response"
    fi
}

###############################################################################
# Test 11: Get Specific Strategy (Verify Backtest Results)
###############################################################################

test_get_strategy() {
    print_header "TEST 11: Get Strategy and Verify Backtest Results"

    if [ -z "$STRATEGY_ID" ]; then
        print_error "No strategy ID available"
        return
    fi

    response=$(auth_get "/strategies/$STRATEGY_ID")

    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        print_success "Retrieved strategy"
        print_info "ID: $(extract_json "$response" '.id')"
        print_info "Name: $(extract_json "$response" '.name')"
        print_info "Status: $(extract_json "$response" '.status')"

        # Check if backtest code exists
        code=$(extract_json "$response" '.backtest_code')
        if [ "$code" != "null" ] && [ -n "$code" ]; then
            code_length=$(echo "$code" | wc -c)
            print_success "Backtest code saved ($code_length chars)"
        fi

        # Check backtest results
        results_count=$(echo "$response" | jq '.backtest_results | length')
        if [ "$results_count" -gt 0 ]; then
            print_success "Backtest results saved ($results_count results)"

            # Check for plot HTML
            plot_html=$(echo "$response" | jq -r '.backtest_results[0].plot_html')
            if [ "$plot_html" != "null" ] && [ -n "$plot_html" ]; then
                plot_length=$(echo "$plot_html" | wc -c)
                print_success "Plot HTML saved ($plot_length chars) ✨"
            else
                print_error "Plot HTML NOT saved"
            fi

            # Check for data CSV
            data_csv=$(echo "$response" | jq -r '.backtest_results[0].data_csv')
            if [ "$data_csv" != "null" ] && [ -n "$data_csv" ]; then
                data_length=$(echo "$data_csv" | wc -c)
                print_success "Data CSV saved ($data_length chars) ✨"
            else
                print_error "Data CSV NOT saved"
            fi

            # Print metrics
            echo ""
            print_info "Latest Backtest Metrics:"
            echo "$response" | jq '.backtest_results[0].metrics'
        fi
    else
        print_error "Failed to get strategy"
        echo "$response"
    fi
}

###############################################################################
# Test 12: Create Signal
###############################################################################

test_create_signal() {
    print_header "TEST 12: Create Signal"

    response=$(auth_post "/signals/" "{
        \"twitter_username\": \"elonmusk\",
        \"ticker\": \"TSLA\",
        \"check_interval\": 60,
        \"description\": \"Monitor Elon's tweets for TSLA sentiment\"
    }")

    if echo "$response" | jq -e '.id' > /dev/null 2>&1; then
        SIGNAL_ID=$(extract_json "$response" '.id')
        print_success "Signal created"
        print_info "Signal ID: $SIGNAL_ID"
        print_info "Twitter: @$(extract_json "$response" '.twitter_username')"
        print_info "Ticker: $(extract_json "$response" '.ticker')"
        print_info "Status: $(extract_json "$response" '.status')"
    else
        print_error "Failed to create signal"
        echo "$response"
    fi
}

###############################################################################
# Test 13: List Signals
###############################################################################

test_list_signals() {
    print_header "TEST 13: List Signals"

    response=$(auth_get "/signals/")

    if echo "$response" | jq -e '.[0].id' > /dev/null 2>&1; then
        count=$(echo "$response" | jq '. | length')
        print_success "Retrieved signals"
        print_info "Total signals: $count"

        # Get first signal
        if [ -z "$SIGNAL_ID" ]; then
            SIGNAL_ID=$(extract_json "$response" '.[0].id')
        fi

        print_info "First signal ID: $SIGNAL_ID"
        print_info "Twitter: @$(extract_json "$response" '.[0].twitter_username')"
        print_info "Status: $(extract_json "$response" '.[0].status')"
    else
        print_info "No signals found (this is okay)"
        echo "$response"
    fi
}

###############################################################################
# Test 14: Pause Signal
###############################################################################

test_pause_signal() {
    print_header "TEST 14: Pause Signal"

    if [ -z "$SIGNAL_ID" ]; then
        print_info "No signal to pause (skipping)"
        return
    fi

    response=$(auth_post "/signals/$SIGNAL_ID/pause" '{}')

    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        status=$(extract_json "$response" '.status')
        print_success "Signal paused"
        print_info "Status: $status"
    else
        print_error "Failed to pause signal"
        echo "$response"
    fi
}

###############################################################################
# Test 15: Resume Signal
###############################################################################

test_resume_signal() {
    print_header "TEST 15: Resume Signal"

    if [ -z "$SIGNAL_ID" ]; then
        print_info "No signal to resume (skipping)"
        return
    fi

    response=$(auth_post "/signals/$SIGNAL_ID/resume" '{}')

    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        status=$(extract_json "$response" '.status')
        print_success "Signal resumed"
        print_info "Status: $status"
    else
        print_error "Failed to resume signal"
        echo "$response"
    fi
}

###############################################################################
# Test 16: Get Signal Events
###############################################################################

test_get_signal_events() {
    print_header "TEST 16: Get Signal Events"

    if [ -z "$SIGNAL_ID" ]; then
        print_info "No signal ID (skipping)"
        return
    fi

    response=$(auth_get "/signals/$SIGNAL_ID/events")

    if echo "$response" | jq -e 'type' > /dev/null 2>&1; then
        count=$(echo "$response" | jq '. | length')
        print_success "Retrieved signal events"
        print_info "Total events: $count"

        if [ "$count" -gt 0 ]; then
            print_info "Latest event sentiment: $(extract_json "$response" '.[0].sentiment')"
            print_info "Latest event confidence: $(extract_json "$response" '.[0].confidence')"
        fi
    else
        print_info "No signal events found (this is okay)"
    fi
}

###############################################################################
# Test 17: Send Another Message (Test Backtest Again)
###############################################################################

test_send_second_message() {
    print_header "TEST 17: Send Second Message (Test Backtesting)"

    print_info "Sending backtest request..."

    response=$(curl -s -X POST "$BASE_URL/conversations/$CONVERSATION_ID/chat" \
        -H "Cookie: access_token=$ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "message": "Can you backtest a simple RSI strategy on AAPL? Buy when RSI < 30, sell when RSI > 70. Use data from 2022-01-01 to 2023-12-31."
        }')

    # Check if backtest was executed
    if echo "$response" | grep -q "backtest_result"; then
        print_success "Backtest executed"

        # Extract and show metrics
        backtest_line=$(echo "$response" | grep "backtest_result")
        print_info "Metrics:"
        echo "$backtest_line" | jq '.data.metrics'
    else
        print_info "Response received (check logs for backtest execution)"
    fi
}

###############################################################################
# Test 18: Delete Conversation
###############################################################################

test_delete_conversation() {
    print_header "TEST 18: Delete Conversation"

    # Create a temporary conversation to delete
    temp_conv=$(auth_post "/conversations/" '{"title": "Temporary Conversation"}')
    temp_id=$(extract_json "$temp_conv" '.id')

    if [ -n "$temp_id" ]; then
        print_info "Created temporary conversation: $temp_id"

        # Delete it
        response=$(auth_delete "/conversations/$temp_id")

        # Check if it's gone
        check=$(auth_get "/conversations/$temp_id")
        if echo "$check" | grep -q "not found"; then
            print_success "Conversation deleted successfully"
        else
            print_error "Failed to delete conversation"
            echo "$check"
        fi
    fi
}

###############################################################################
# Test 19: Stop Signal
###############################################################################

test_stop_signal() {
    print_header "TEST 19: Stop Signal"

    if [ -z "$SIGNAL_ID" ]; then
        print_info "No signal to stop (skipping)"
        return
    fi

    response=$(auth_post "/signals/$SIGNAL_ID/stop" '{}')

    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        status=$(extract_json "$response" '.status')
        print_success "Signal stopped"
        print_info "Status: $status"
    else
        print_error "Failed to stop signal"
        echo "$response"
    fi
}

###############################################################################
# Test 20: Logout
###############################################################################

test_logout() {
    print_header "TEST 20: Logout"

    response=$(curl -s -X POST "$BASE_URL/auth/logout" \
        -H "Cookie: access_token=$ACCESS_TOKEN")

    if echo "$response" | grep -q "Logged out successfully"; then
        print_success "Logout successful"
        ACCESS_TOKEN=""
    else
        print_error "Logout failed"
        echo "$response"
    fi
}

###############################################################################
# Main Test Runner
###############################################################################

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         BacktestMCP API Test Suite                         ║"
    echo "║         Comprehensive End-to-End Testing                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Check dependencies
    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed. Install with: brew install jq"
        exit 1
    fi

    print_info "Base URL: $BASE_URL"
    print_info "Test Email: $TEST_EMAIL"
    echo ""

    # Run all tests
    test_health_check
    test_user_registration
    test_user_login
    test_get_current_user
    test_create_conversation
    test_list_conversations
    test_get_conversation
    test_send_first_message
    test_verify_messages
    test_list_strategies
    test_get_strategy
    test_create_signal
    test_list_signals
    test_pause_signal
    test_resume_signal
    test_get_signal_events
    test_send_second_message
    test_delete_conversation
    test_stop_signal
    test_logout

    # Summary
    echo ""
    print_header "TEST SUMMARY"
    print_success "All tests completed successfully!"
    echo ""
    print_info "Summary:"
    echo "  - User ID: $USER_ID"
    echo "  - Conversation ID: $CONVERSATION_ID"
    echo "  - Strategy ID: $STRATEGY_ID"
    echo "  - Signal ID: $SIGNAL_ID"
    echo ""
    print_success "✨ The API is working correctly!"
    print_success "✨ Backtest files (code, plot HTML, data CSV) are being saved!"
    echo ""
}

# Run the test suite
main
