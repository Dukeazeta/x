import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime
import threading
import time
from collections import deque
from indicators import calculate_indicators
from signal_generator import generate_signals

class MexcWebSocketStream:
    def __init__(self, symbol, interval='Min15', max_candles=1000):
        self.symbol = symbol
        self.interval = interval
        self.max_candles = max_candles
        self.candle_buffer = deque(maxlen=max_candles)
        self.is_running = False
        self.callbacks = []
        self.last_signal = None
        self.last_signal_time = None
        
        # WebSocket URL for MEXC futures (updated endpoint)
        self.ws_url = "wss://contract.mexc.com/edge"
        
    def add_callback(self, callback):
        """Add callback function to be called on new signals"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove callback function"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def connect_and_stream(self):
        """Connect to WebSocket and start streaming"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Subscribe to kline data
                subscribe_msg = {
                    "method": "sub.kline",
                    "param": {
                        "symbol": self.symbol,
                        "interval": self.interval
                    }
                }
                
                await websocket.send(json.dumps(subscribe_msg))
                print(f"🔗 Connected to MEXC WebSocket for {self.symbol} ({self.interval})")
                
                self.is_running = True
                
                async for message in websocket:
                    if not self.is_running:
                        break
                        
                    try:
                        data = json.loads(message)
                        await self.process_message(data)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.is_running = False
    
    async def process_message(self, data):
        """Process incoming WebSocket message"""
        # Handle different message types
        if data.get('channel') == 'push.kline' and 'data' in data:
            kline_data = data['data']

            # Extract OHLCV data from MEXC format
            candle = {
                'timestamp': pd.to_datetime(kline_data['t'], unit='s'),
                'open': float(kline_data['o']),
                'high': float(kline_data['h']),
                'low': float(kline_data['l']),
                'close': float(kline_data['c']),
                'volume': float(kline_data['q'])  # 'q' is volume in MEXC format
            }

            # Add to buffer
            self.candle_buffer.append(candle)

            # Process signals if we have enough data
            if len(self.candle_buffer) >= 50:  # Minimum for indicators
                await self.analyze_signals()

        elif data.get('channel') == 'rs.sub.kline':
            if data.get('data') == 'success':
                print(f"✅ Successfully subscribed to {self.symbol} kline data")
            else:
                print(f"❌ Failed to subscribe: {data.get('data')}")

        elif data.get('channel') == 'pong':
            # Handle pong response
            pass

        elif data.get('channel') == 'rs.error':
            print(f"❌ WebSocket error: {data.get('data')}")
    
    async def analyze_signals(self):
        """Analyze current data and generate signals"""
        try:
            # Convert buffer to DataFrame
            df = pd.DataFrame(list(self.candle_buffer))
            df.set_index('timestamp', inplace=True)
            
            # Calculate indicators
            df = calculate_indicators(df)
            
            # Generate signals
            df = generate_signals(df, use_price_action=True)
            
            # Get latest signal
            latest_row = df.iloc[-1]
            current_signal = latest_row['signal']
            signal_strength = latest_row['signal_strength']
            signal_reason = latest_row['signal_reason']
            
            # Check if signal changed
            if current_signal != 0 and current_signal != self.last_signal:
                signal_data = {
                    'symbol': self.symbol,
                    'interval': self.interval,
                    'timestamp': df.index[-1],
                    'signal': 'BUY' if current_signal == 1 else 'SELL',
                    'signal_strength': signal_strength,
                    'signal_reason': signal_reason,
                    'price': latest_row['close'],
                    'rsi': latest_row.get('RSI_14', None),
                    'macd': latest_row.get('MACD_12_26_9', None),
                    'adx': latest_row.get('ADX_14', None)
                }
                
                # Call all registered callbacks
                for callback in self.callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(signal_data)
                        else:
                            callback(signal_data)
                    except Exception as e:
                        print(f"Error in callback: {e}")
                
                self.last_signal = current_signal
                self.last_signal_time = datetime.now()
                
        except Exception as e:
            print(f"Error analyzing signals: {e}")
    
    def start_streaming(self):
        """Start streaming in a separate thread"""
        def run_stream():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_and_stream())
        
        thread = threading.Thread(target=run_stream, daemon=True)
        thread.start()
        return thread
    
    def stop_streaming(self):
        """Stop the WebSocket stream"""
        self.is_running = False
        print(f"🛑 Stopped streaming for {self.symbol}")

class MultiSymbolStream:
    """Manage multiple WebSocket streams for different symbols"""
    
    def __init__(self):
        self.streams = {}
        self.global_callbacks = []
    
    def add_symbol(self, symbol, interval='Min15'):
        """Add a symbol to stream"""
        if symbol not in self.streams:
            stream = MexcWebSocketStream(symbol, interval)
            
            # Add global callbacks to this stream
            for callback in self.global_callbacks:
                stream.add_callback(callback)
            
            self.streams[symbol] = stream
            return stream
        return self.streams[symbol]
    
    def remove_symbol(self, symbol):
        """Remove a symbol from streaming"""
        if symbol in self.streams:
            self.streams[symbol].stop_streaming()
            del self.streams[symbol]
    
    def add_global_callback(self, callback):
        """Add callback to all streams"""
        self.global_callbacks.append(callback)
        for stream in self.streams.values():
            stream.add_callback(callback)
    
    def start_all_streams(self):
        """Start all streams"""
        threads = []
        for symbol, stream in self.streams.items():
            thread = stream.start_streaming()
            threads.append(thread)
            print(f"🚀 Started streaming for {symbol}")
        return threads
    
    def stop_all_streams(self):
        """Stop all streams"""
        for stream in self.streams.values():
            stream.stop_streaming()
        self.streams.clear()

# Example callback functions
def print_signal_callback(signal_data):
    """Simple callback that prints signals to console"""
    timestamp = signal_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    symbol = signal_data['symbol']
    signal = signal_data['signal']
    strength = signal_data['signal_strength']
    price = signal_data['price']
    
    print(f"\n🚨 LIVE SIGNAL ALERT 🚨")
    print(f"Symbol: {symbol}")
    print(f"Signal: {signal}")
    print(f"Strength: {strength:.3f}")
    print(f"Price: ${price:,.2f}")
    print(f"Time: {timestamp}")
    print("-" * 40)

async def async_signal_callback(signal_data):
    """Async callback example"""
    # Could send to Discord, Telegram, etc.
    print(f"📡 Async processing signal for {signal_data['symbol']}: {signal_data['signal']}")

# Example usage
if __name__ == "__main__":
    # Single symbol streaming
    stream = MexcWebSocketStream('BTC_USDT', 'Min15')
    stream.add_callback(print_signal_callback)
    
    print("Starting real-time signal monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        thread = stream.start_streaming()
        
        # Keep main thread alive
        while stream.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping stream...")
        stream.stop_streaming()
        print("Stream stopped.")
