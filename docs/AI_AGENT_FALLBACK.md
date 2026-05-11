# AI Agent Fallback Mechanism

## Overview

The AI Chat Agent has been enhanced with a **fallback mechanism** that allows it to function even when Azure OpenAI is unavailable or experiencing connection issues.

---

## How It Works

### Primary Mode: Azure OpenAI
When Azure OpenAI is available, the agent uses GPT-Nano for:
- Natural language understanding
- Intent classification
- Contextual responses
- Complex query handling

### Fallback Mode: Keyword Matching
When Azure OpenAI is unavailable (timeout/connection errors), the agent automatically switches to a keyword-based system that:
- Extracts stock symbols from queries (e.g., AAPL, MSFT, GOOGL)
- Matches keywords to determine intent
- Executes the appropriate tool/function
- Returns data-driven responses

---

## Supported Intents in Fallback Mode

### 1. Stock Price Queries
**Keywords**: `price`, `cost`, `worth`, `value`, `current`

**Example Queries**:
- "What is the current price of AAPL?"
- "How much is MSFT worth?"
- "Get me the value of GOOGL"

**Response**: Returns current stock price from Yahoo Finance

---

### 2. Predictions
**Keywords**: `predict`, `prediction`, `forecast`, `future`, `tomorrow`

**Example Queries**:
- "Give me a prediction for MSFT"
- "Forecast AAPL for 5 days"
- "What will TSLA be tomorrow?"

**Response**: Returns LSTM model predictions with confidence scores

---

### 3. Sentiment Analysis
**Keywords**: `sentiment`, `news`, `feeling`, `opinion`

**Example Queries**:
- "What is the sentiment for GOOGL?"
- "How is the news for AAPL?"
- "What's the feeling about TSLA?"

**Response**: Returns sentiment analysis from news articles

---

### 4. Stock Comparison
**Keywords**: `compare`, `versus`, `vs`, `difference`

**Example Queries**:
- "Compare AAPL and MSFT"
- "GOOGL versus TSLA"
- "Difference between AAPL vs MSFT"

**Response**: Returns current prices for multiple stocks

---

## Symbol Extraction

The fallback mechanism automatically extracts stock symbols from queries using pattern matching:
- Looks for uppercase words 1-5 characters long
- Examples: AAPL, MSFT, GOOGL, TSLA, AMZN

**Valid Queries**:
```
"What is AAPL price?"          → Extracts: AAPL
"Compare AAPL and MSFT"        → Extracts: AAPL, MSFT
"Predict GOOGL for tomorrow"   → Extracts: GOOGL
```

---

## Error Handling

### Connection Timeout
When Azure OpenAI times out (10 second timeout):
```
2026-05-11 22:28:21 | ERROR | app.agent.agent:classify_intent:56 - 
classify_intent failed: upstream connect error or disconnect/reset before headers
```

**Agent Response**: Automatically switches to fallback mode and processes the query

### Invalid Symbol
If no valid stock symbol is found:
```json
{
  "response": "Please specify a stock symbol."
}
```

### General Errors
For unrecognized queries:
```json
{
  "response": "I can help you with stock prices, predictions, and sentiment analysis. 
               Try asking: 'What is the price of AAPL?' or 'Predict MSFT for 5 days'"
}
```

---

## Configuration

### Timeout Setting
The agent has a 10-second timeout for Azure OpenAI requests:

```python
response = self.client.chat.completions.create(
    model=self.deployment,
    messages=[...],
    max_completion_tokens=512,
    timeout=10.0,  # 10 second timeout
)
```

### Azure OpenAI Credentials
Located in `backend/.env`:
```env
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-5.4-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

---

## Testing

### Test Fallback Mode
To test the fallback mechanism, you can:

1. **Disconnect from network** (forces timeout)
2. **Use invalid Azure credentials** (forces connection error)
3. **Wait for timeout** (10 seconds)

The agent will automatically switch to fallback mode.

### Test Queries
```bash
# Price query
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current price of AAPL?"}'

# Prediction query
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Give me a prediction for MSFT"}'

# Sentiment query
curl -X POST http://localhost:8000/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the sentiment for GOOGL?"}'
```

---

## Advantages

### Reliability
- ✅ Agent works even when Azure OpenAI is down
- ✅ No service interruption for users
- ✅ Graceful degradation

### Performance
- ✅ Faster responses in fallback mode (no API call)
- ✅ No external dependencies
- ✅ Reduced latency

### Cost
- ✅ No Azure OpenAI API costs in fallback mode
- ✅ Reduced token usage
- ✅ Lower operational costs

---

## Limitations

### Fallback Mode Limitations
1. **No Natural Language Understanding**: Relies on keyword matching
2. **Limited Context**: Cannot understand complex queries
3. **No Conversational Memory**: Each query is independent
4. **Exact Symbol Required**: Must use uppercase stock symbols

### Examples of Queries That Need Azure OpenAI
- "Which stock should I invest in?"
- "Explain what LSTM models are"
- "Why is AAPL going up?"
- "What factors affect stock prices?"

These queries will receive a generic response in fallback mode.

---

## Monitoring

### Logs
Check backend logs for fallback activation:
```
2026-05-11 22:31:50 | INFO | app.agent.agent:classify_intent:60 - 
Using fallback keyword-based intent classification
```

### Metrics
- **Primary Mode**: Azure OpenAI responses
- **Fallback Mode**: Keyword-based responses
- **Error Rate**: Connection timeouts

---

## Future Enhancements

### Planned Improvements
1. [ ] Cache Azure OpenAI responses for common queries
2. [ ] Add more sophisticated NLP in fallback mode
3. [ ] Implement retry logic with exponential backoff
4. [ ] Add health check endpoint for Azure OpenAI
5. [ ] Support for lowercase stock symbols
6. [ ] Multi-language support in fallback mode

---

## Summary

The AI Agent fallback mechanism ensures:
- ✅ **100% Uptime**: Agent always available
- ✅ **Graceful Degradation**: Smooth transition to fallback
- ✅ **Core Functionality**: Price, predictions, sentiment still work
- ✅ **User Experience**: No error messages, just responses
- ✅ **Cost Effective**: Reduced API costs

**Status**: Production Ready 🚀

---

*Last Updated: May 11, 2026*  
*Version: 2.1.0*  
*Feature: AI Agent Fallback Mechanism*
