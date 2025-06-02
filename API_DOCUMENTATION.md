# Crypto Signal Generator API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for local development.

## Endpoints

### 1. Get API Information
```http
GET /
```

**Response:**
```json
{
  "message": "Crypto Signal Generator API",
  "version": "1.0.0",
  "endpoints": {
    "symbols": "/symbols",
    "search": "/symbols/search/{query}",
    "signal": "/signal",
    "mtf": "/mtf",
    "backtest": "/backtest/{symbol}",
    "stream": "/ws/stream"
  }
}
```

### 2. Get Trading Symbols (with metadata)
```http
GET /symbols?limit=50
```

**Parameters:**
- `limit` (optional): Number of symbols to return (default: 50)

**Response:**
```json
{
  "symbols": ["BTC_USDT", "ETH_USDT", "BNB_USDT", ...],
  "total_available": 782,
  "message": "Retrieved 50 popular symbols"
}
```

### 2b. Get Trading Symbols (simple list)
```http
GET /symbols/list?limit=50
```

**Parameters:**
- `limit` (optional): Number of symbols to return (default: 50)

**Response:**
```json
["BTC_USDT", "ETH_USDT", "BNB_USDT", "XRP_USDT", "ADA_USDT"]
```

**Note:** Use `/symbols/list` for Flutter apps that expect a direct array response.

### 3. Search Symbols
```http
GET /symbols/search/{query}?max_results=10
```

**Parameters:**
- `query`: Search term (e.g., "btc", "eth")
- `max_results` (optional): Maximum results (default: 10)

**Response:**
```json
{
  "query": "btc",
  "matches": ["BTC_USDT", "BTC_USD"],
  "count": 2
}
```

### 4. Get Symbol Information
```http
GET /symbols/{symbol}/info
```

**Response:**
```json
{
  "symbol": "BTC_USDT",
  "display_name": "BTC_USDT PERPETUAL",
  "base_coin": "BTC",
  "quote_coin": "USDT",
  "max_leverage": 500,
  "current_data": {
    "price": 105604.3,
    "volume": 182876.0,
    "high_24h": 105896.0,
    "low_24h": 103616.7,
    "timestamp": "2025-06-02T23:00:00"
  }
}
```

### 5. Get Trading Signal
```http
POST /signal
```

**Request Body:**
```json
{
  "symbol": "BTC_USDT",
  "interval": "Min15",
  "use_price_action": true,
  "use_ml": false
}
```

**Response:**
```json
{
  "symbol": "BTC_USDT",
  "timestamp": "2025-06-02T23:00:00",
  "signal": "HOLD",
  "signal_strength": 0.02,
  "signal_reason": "Neutral (Score: 0.20)",
  "price": 105630.5,
  "rsi": 66.48,
  "macd": 320.15,
  "adx": 25.88,
  "support_level": 105580.9,
  "resistance_level": 105754.3,
  "trend_structure": "uptrend",
  "volume": 182876.0,
  "change_24h": 1250.5,
  "change_percent_24h": 1.2
}
```

### 6. Multi-Timeframe Analysis
```http
POST /mtf
```

**Request Body:**
```json
{
  "symbol": "BTC_USDT",
  "timeframes": ["Min15", "Min60", "Hour4"],
  "use_price_action": true
}
```

**Response:**
```json
{
  "symbol": "BTC_USDT",
  "final_signal": "HOLD",
  "confluence_score": 0.0,
  "signal_strength": 0.0,
  "trend_consensus": "sideways",
  "trend_agreement": 0.67,
  "timeframes_analyzed": 3,
  "timeframe_breakdown": {
    "Min15": {
      "signal": 0,
      "signal_strength": 0.015,
      "signal_reason": "Neutral",
      "trend_structure": "uptrend",
      "rsi": 69.15,
      "macd": 223.06,
      "adx": 21.96,
      "price": 105557.5,
      "timestamp": "2025-06-02T22:45:00",
      "support_level": 105480.1,
      "resistance_level": 105754.3
    }
  }
}
```

### 7. Backtest
```http
GET /backtest/{symbol}?initial_balance=10000
```

**Parameters:**
- `symbol`: Trading pair symbol
- `initial_balance` (optional): Starting balance (default: 10000)

**Response:**
```json
{
  "symbol": "BTC_USDT",
  "initial_balance": 10000.0,
  "final_balance": 10250.5,
  "total_return": 2.51,
  "max_drawdown": -5.2,
  "total_trades": 15,
  "win_rate": 60.0
}
```

### 8. WebSocket Streaming
```
ws://localhost:8000/ws/stream
```

**Subscribe Message:**
```json
{
  "action": "subscribe",
  "symbols": ["BTC_USDT", "ETH_USDT"],
  "interval": "Min15"
}
```

**Signal Message (Received):**
```json
{
  "type": "signal",
  "data": {
    "symbol": "BTC_USDT",
    "interval": "Min15",
    "timestamp": "2025-06-02T23:00:00",
    "signal": "BUY",
    "signal_strength": 0.75,
    "signal_reason": "Bullish confluence",
    "price": 105630.5,
    "rsi": 66.48,
    "macd": 320.15,
    "adx": 25.88
  }
}
```

**Unsubscribe Message:**
```json
{
  "action": "unsubscribe"
}
```

## Signal Types
- `BUY`: Bullish signal (value: 1)
- `SELL`: Bearish signal (value: -1)  
- `HOLD`: Neutral signal (value: 0)

## Intervals
- `Min1`: 1 minute
- `Min5`: 5 minutes
- `Min15`: 15 minutes (default)
- `Min30`: 30 minutes
- `Min60`: 1 hour
- `Hour4`: 4 hours
- `Hour8`: 8 hours
- `Day1`: 1 day

## Error Responses
```json
{
  "detail": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (symbol/data not available)
- `500`: Internal Server Error

## Rate Limiting
No rate limiting implemented for local development.

## CORS
CORS is enabled for all origins during development.
