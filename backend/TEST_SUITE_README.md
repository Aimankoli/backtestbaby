# BacktestMCP API Test Suite

Comprehensive testing tools for the BacktestMCP API using curl.

## 📋 Prerequisites

### Required Tools
- **curl** - Command-line HTTP client (pre-installed on macOS)
- **jq** - JSON processor for parsing responses

### Install jq
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Check installation
jq --version
```

### API Server
Ensure the API server is running:
```bash
cd /Users/saroopmakhija/backtestbaby/backend
uvicorn app.main:app --reload
```

The API should be accessible at `http://localhost:8000`

## 🚀 Test Scripts

### 1. Quick Test (`quick_test.sh`)
**Fast 5-test suite for rapid verification**

```bash
./quick_test.sh
```

**What it tests:**
1. ✅ Health check endpoint
2. ✅ User registration & login
3. ✅ Conversation creation
4. ✅ Backtest execution via chat
5. ✅ Strategy file storage (code, plot HTML, data CSV)

**Duration:** ~30-60 seconds

**Use when:**
- Testing after code changes
- Quick smoke test
- Verifying file storage works

---

### 2. Comprehensive Test Suite (`test_api.sh`)
**Full 20-test suite covering all endpoints**

```bash
./test_api.sh
```

**What it tests:**
1. ✅ Health check
2. ✅ User registration
3. ✅ User login
4. ✅ Get current user
5. ✅ Create conversation
6. ✅ List conversations
7. ✅ Get specific conversation
8. ✅ Send first chat message (creates strategy)
9. ✅ Verify messages saved
10. ✅ List strategies
11. ✅ Get strategy (verify backtest results & files)
12. ✅ Create signal
13. ✅ List signals
14. ✅ Pause signal
15. ✅ Resume signal
16. ✅ Get signal events
17. ✅ Send second message (test backtesting)
18. ✅ Delete conversation
19. ✅ Stop signal
20. ✅ Logout

**Duration:** ~2-3 minutes

**Use when:**
- Full API verification
- Before deployment
- Testing all features

---

## 📊 What Gets Tested

### File Storage Verification ✨

Both test suites verify that **backtest files are saved to the database**:

1. **Backtest Code** - The generated Python script
2. **Plot HTML** - Interactive Bokeh chart (complete HTML file)
3. **Data CSV** - Historical stock data used

**Example output:**
```
✓ Backtest code saved (2847 bytes)
✓ Plot HTML saved (156234 bytes) ✨
✓ Data CSV saved (45678 bytes) ✨
```

### API Endpoints Covered

**Authentication:**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (cookie-based)
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

**Conversations:**
- `POST /conversations/` - Create conversation
- `GET /conversations/` - List user conversations
- `GET /conversations/{id}` - Get specific conversation
- `POST /conversations/{id}/chat` - Send message (streaming)
- `DELETE /conversations/{id}` - Delete conversation

**Strategies:**
- `GET /strategies/` - List user strategies
- `GET /strategies/{id}` - Get specific strategy
- `POST /strategies/` - Create strategy
- `PATCH /strategies/{id}` - Update strategy
- `DELETE /strategies/{id}` - Delete strategy

**Signals:**
- `POST /signals/` - Create signal
- `GET /signals/` - List signals
- `GET /signals/{id}` - Get specific signal
- `POST /signals/{id}/pause` - Pause signal
- `POST /signals/{id}/resume` - Resume signal
- `POST /signals/{id}/stop` - Stop signal
- `GET /signals/{id}/events` - Get signal events

---

## 🔍 Manual Testing Examples

### Test Health Check
```bash
curl http://localhost:8000/
```

### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Login
```bash
curl -i -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

**Extract token from response:**
```
Set-Cookie: access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Create Conversation (Authenticated)
```bash
TOKEN="your-token-here"

curl -X POST "http://localhost:8000/conversations/" \
  -H "Cookie: access_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Strategy"}'
```

### Send Chat Message
```bash
CONV_ID="your-conversation-id"

curl -X POST "http://localhost:8000/conversations/$CONV_ID/chat" \
  -H "Cookie: access_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Backtest a MA crossover strategy on SPY from 2022-01-01 to 2023-01-01"
  }'
```

**Response format (streaming):**
```json
{"type": "content", "data": "I'll help you backtest..."}
{"type": "strategy_created", "data": {"strategy_id": "...", "name": "..."}}
{"type": "backtest_result", "data": {"metrics": {...}}}
{"type": "done"}
```

### Get Strategy
```bash
STRATEGY_ID="your-strategy-id"

curl -X GET "http://localhost:8000/strategies/$STRATEGY_ID" \
  -H "Cookie: access_token=$TOKEN" | jq '.'
```

**Check for saved files:**
```bash
# Get backtest code
curl -s -X GET "http://localhost:8000/strategies/$STRATEGY_ID" \
  -H "Cookie: access_token=$TOKEN" | jq -r '.backtest_code'

# Get plot HTML
curl -s -X GET "http://localhost:8000/strategies/$STRATEGY_ID" \
  -H "Cookie: access_token=$TOKEN" | jq -r '.backtest_results[0].plot_html'

# Get data CSV
curl -s -X GET "http://localhost:8000/strategies/$STRATEGY_ID" \
  -H "Cookie: access_token=$TOKEN" | jq -r '.backtest_results[0].data_csv'
```

### Create Signal
```bash
curl -X POST "http://localhost:8000/signals/" \
  -H "Cookie: access_token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "twitter_username": "elonmusk",
    "ticker": "TSLA",
    "check_interval": 60,
    "description": "Monitor Elon tweets for TSLA sentiment"
  }'
```

### List Signal Events
```bash
SIGNAL_ID="your-signal-id"

curl -X GET "http://localhost:8000/signals/$SIGNAL_ID/events" \
  -H "Cookie: access_token=$TOKEN" | jq '.'
```

---

## 🐛 Debugging

### Enable Verbose Output
```bash
# Add -v flag to curl for debugging
curl -v http://localhost:8000/
```

### Check API Logs
```bash
# Watch API server logs in real-time
tail -f /path/to/api/logs
```

### Common Issues

**1. Connection Refused**
```
curl: (7) Failed to connect to localhost port 8000
```
**Solution:** Ensure API server is running:
```bash
uvicorn app.main:app --reload
```

**2. 401 Unauthorized**
```
{"detail": "Not authenticated"}
```
**Solution:** Check your access token is valid and included in Cookie header

**3. jq command not found**
```
bash: jq: command not found
```
**Solution:** Install jq:
```bash
brew install jq
```

**4. Test script permission denied**
```
bash: ./test_api.sh: Permission denied
```
**Solution:** Make script executable:
```bash
chmod +x test_api.sh quick_test.sh
```

---

## 📈 Expected Results

### Successful Test Output

**Quick Test:**
```
=== Quick API Test ===

1. Testing health endpoint...
✓ API is running

2. Testing authentication...
✓ Authentication successful

3. Creating conversation...
✓ Conversation created: 673d5f2a8b1c9d3f4e2a1b0c

4. Testing backtest (this may take 30-60 seconds)...
✓ Backtest executed successfully

Metrics:
{
  "total_return": 7.32,
  "buy_hold_return": 43.6,
  "max_drawdown": -7.07,
  "sharpe_ratio": 0.42,
  "num_trades": 1,
  "win_rate": 100
}

5. Verifying strategy and files...
✓ Backtest code saved (2847 bytes)
✓ Plot HTML saved (156234 bytes) ✨
✓ Data CSV saved (45678 bytes) ✨

========================================
✨ Quick test completed!
========================================
```

**Comprehensive Test:**
```
╔════════════════════════════════════════════════════════════╗
║         BacktestMCP API Test Suite                         ║
║         Comprehensive End-to-End Testing                   ║
╚════════════════════════════════════════════════════════════╝

========================================
TEST 1: Health Check
========================================
✓ Health check passed

... [all 20 tests] ...

========================================
TEST SUMMARY
========================================
✓ All tests completed successfully!

Summary:
  - User ID: 673d5f2a8b1c9d3f4e2a1b0c
  - Conversation ID: 673d5f2b8b1c9d3f4e2a1b0d
  - Strategy ID: 673d5f2c8b1c9d3f4e2a1b0e
  - Signal ID: 673d5f2d8b1c9d3f4e2a1b0f

✨ The API is working correctly!
✨ Backtest files (code, plot HTML, data CSV) are being saved!
```

---

## 🔐 Authentication Flow

The API uses **HTTP-only cookie-based authentication**:

1. **Register:** `POST /auth/register`
2. **Login:** `POST /auth/login` → Returns `Set-Cookie: access_token=...`
3. **Authenticated requests:** Include `Cookie: access_token=...` header
4. **Logout:** `POST /auth/logout`

**Security Features:**
- JWT tokens in HTTP-only cookies
- 1-day token expiration
- Secure flag in production
- SameSite protection

---

## 📝 File Storage Verification

The key improvement is that **all backtest files are now saved to the database**:

### Before (Problem):
```json
{
  "backtest_results": [{
    "plot_path": "/tmp/backtest_data/SPY_results.html",  // ❌ Frontend can't access
    "metrics": {...}
  }]
}
```

### After (Fixed):
```json
{
  "backtest_code": "from backtesting import Strategy...",  // ✅ Full Python code
  "backtest_results": [{
    "plot_path": "/tmp/backtest_data/SPY_results.html",
    "plot_html": "<!DOCTYPE html><html>...",  // ✅ Complete HTML
    "data_csv": "Date,Open,High,Low,Close,Volume\n...",  // ✅ Complete CSV
    "metrics": {...}
  }]
}
```

**Frontend can now:**
1. Display backtest code in code editor
2. Render interactive chart from `plot_html`
3. Download or visualize data from `data_csv`

---

## 🎯 Next Steps

After running tests:

1. **Verify in MongoDB:**
   ```bash
   mongosh
   use BacktestMCP
   db.strategies.findOne({}, {backtest_code: 1, backtest_results: 1})
   ```

2. **Test with Frontend:**
   - Load strategy page
   - Verify chart displays
   - Verify code shows in editor
   - Test data download

3. **Monitor Performance:**
   - Check file sizes in database
   - Monitor database growth
   - Consider compression for large files

---

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** `http://localhost:8000/redoc` (ReDoc)
- **MongoDB Compass:** Visual database explorer
- **Postman Collection:** Can import curl commands

---

## ⚡ Quick Reference

```bash
# Start API server
uvicorn app.main:app --reload

# Run quick test
./quick_test.sh

# Run full test suite
./test_api.sh

# Check API is running
curl http://localhost:8000/

# View API docs
open http://localhost:8000/docs

# Check MongoDB
mongosh
use BacktestMCP
db.strategies.find().pretty()
```

---

**Happy Testing! 🚀**
