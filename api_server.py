from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime
import uvicorn

# Import your existing modules
from data_fetcher import fetch_candles
from indicators import calculate_indicators
from signal_generator import generate_signals, ml_signal_generator, multi_timeframe_analysis, calculate_mtf_confluence
from symbol_manager import symbol_manager
from websocket_stream import MexcWebSocketStream, MultiSymbolStream
from backtest import simple_backtest

# Pydantic models for API requests/responses
class SymbolRequest(BaseModel):
    symbol: str
    interval: str = "Min15"
    use_price_action: bool = True
    use_ml: bool = False

class MTFRequest(BaseModel):
    symbol: str
    timeframes: List[str] = ["Min15", "Min60", "Hour4"]
    use_price_action: bool = True

class StreamRequest(BaseModel):
    symbols: List[str]
    interval: str = "Min15"

class SignalResponse(BaseModel):
    symbol: str
    timestamp: str
    signal: str
    signal_strength: float
    signal_reason: str
    price: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    adx: Optional[float] = None
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    trend_structure: Optional[str] = None

class MTFResponse(BaseModel):
    symbol: str
    final_signal: str
    confluence_score: float
    signal_strength: float
    trend_consensus: str
    trend_agreement: float
    timeframes_analyzed: int
    timeframe_breakdown: Dict[str, Any]

class BacktestResponse(BaseModel):
    symbol: str
    initial_balance: float
    final_balance: float
    total_return: float
    max_drawdown: float
    total_trades: int
    win_rate: float

# Initialize FastAPI app
app = FastAPI(
    title="Crypto Signal Generator API",
    description="Professional crypto trading signal generator with multi-timeframe analysis and real-time streaming",
    version="1.0.0"
)

# Add CORS middleware for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for WebSocket management
active_connections: List[WebSocket] = []
stream_manager = MultiSymbolStream()

@app.get("/")
async def root():
    return {
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

@app.get("/symbols")
async def get_symbols(limit: int = 50):
    """Get list of available trading symbols"""
    try:
        symbols = symbol_manager.get_popular_symbols(limit)
        return {
            "symbols": symbols,
            "total_available": len(symbol_manager.get_all_symbols()),
            "message": f"Retrieved {len(symbols)} popular symbols"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/symbols/search/{query}")
async def search_symbols(query: str, max_results: int = 10):
    """Search for symbols matching query"""
    try:
        matches = symbol_manager.fuzzy_search(query, max_results)
        return {
            "query": query,
            "matches": matches,
            "count": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signal", response_model=SignalResponse)
async def get_signal(request: SymbolRequest):
    """Get trading signal for a symbol"""
    try:
        # Validate symbol
        symbol, is_valid, message = symbol_manager.validate_symbol(request.symbol)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {message}")
        
        # Fetch data
        df = fetch_candles(symbol, request.interval)
        if df is None or len(df) == 0:
            raise HTTPException(status_code=404, detail="No data available for symbol")
        
        # Calculate indicators
        df = calculate_indicators(df)
        
        # Generate signals
        df = generate_signals(df, use_price_action=request.use_price_action)
        
        # Apply ML if requested
        if request.use_ml:
            df = ml_signal_generator(df)
        
        # Get latest signal
        latest_row = df.iloc[-1]
        
        return SignalResponse(
            symbol=symbol,
            timestamp=latest_row.name.isoformat(),
            signal="BUY" if latest_row['signal'] == 1 else "SELL" if latest_row['signal'] == -1 else "HOLD",
            signal_strength=latest_row['signal_strength'],
            signal_reason=latest_row['signal_reason'],
            price=latest_row['close'],
            rsi=latest_row.get('RSI_14'),
            macd=latest_row.get('MACD_12_26_9'),
            adx=latest_row.get('ADX_14'),
            support_level=latest_row.get('support_level'),
            resistance_level=latest_row.get('resistance_level'),
            trend_structure=latest_row.get('trend_structure')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mtf", response_model=MTFResponse)
async def get_mtf_analysis(request: MTFRequest):
    """Get multi-timeframe analysis"""
    try:
        # Validate symbol
        symbol, is_valid, message = symbol_manager.validate_symbol(request.symbol)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {message}")
        
        # Perform MTF analysis
        mtf_results = multi_timeframe_analysis(
            symbol, 
            timeframes=request.timeframes, 
            use_price_action=request.use_price_action
        )
        
        if not mtf_results:
            raise HTTPException(status_code=404, detail="No MTF data available")
        
        # Calculate confluence
        confluence = calculate_mtf_confluence(mtf_results)
        
        return MTFResponse(
            symbol=symbol,
            final_signal=confluence['final_signal'],
            confluence_score=confluence['confluence_score'],
            signal_strength=confluence['signal_strength'],
            trend_consensus=confluence['trend_consensus'],
            trend_agreement=confluence['trend_agreement'],
            timeframes_analyzed=confluence['timeframes_analyzed'],
            timeframe_breakdown=mtf_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backtest/{symbol}", response_model=BacktestResponse)
async def get_backtest(symbol: str, initial_balance: float = 10000):
    """Run backtest for a symbol"""
    try:
        # Validate symbol
        normalized_symbol, is_valid, message = symbol_manager.validate_symbol(symbol)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid symbol: {message}")
        
        # Run backtest
        results = simple_backtest(normalized_symbol, initial_balance)
        
        if results is None:
            raise HTTPException(status_code=404, detail="Backtest failed - no data available")
        
        return BacktestResponse(
            symbol=normalized_symbol,
            initial_balance=results['initial_balance'],
            final_balance=results['final_balance'],
            total_return=results['total_return'],
            max_drawdown=results['max_drawdown'],
            total_trades=results['total_trades'],
            win_rate=results['win_rate']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time signal streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Wait for client message (symbol subscription)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                symbols = message.get("symbols", [])
                interval = message.get("interval", "Min15")
                
                # Add symbols to stream manager
                for symbol in symbols:
                    normalized_symbol, is_valid, _ = symbol_manager.validate_symbol(symbol)
                    if is_valid:
                        stream_manager.add_symbol(normalized_symbol, interval)
                
                # Add callback to send signals to WebSocket
                async def websocket_callback(signal_data):
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "signal",
                            "data": signal_data
                        }, default=str))
                    except:
                        pass  # Connection might be closed
                
                stream_manager.add_global_callback(websocket_callback)
                
                # Start streaming
                stream_manager.start_all_streams()
                
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": f"Subscribed to {len(symbols)} symbols"
                }))
            
            elif message.get("action") == "unsubscribe":
                stream_manager.stop_all_streams()
                await websocket.send_text(json.dumps({
                    "type": "status", 
                    "message": "Unsubscribed from all streams"
                }))
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        stream_manager.stop_all_streams()

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
