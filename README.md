# Crypto Trading Signal Generator

An AI-powered cryptocurrency trading signal tool that fetches real-time market data from MEXC futures, calculates technical indicators, and generates buy/sell signals using both rule-based strategies and machine learning models.

## Features

- **Real-time Data**: Fetches live cryptocurrency futures data from MEXC API
- **Comprehensive Technical Analysis**: 20+ indicators across 5 categories (trend, momentum, volume, volatility, oscillators)
- **Price Action Analysis**: Candlestick pattern recognition, support/resistance detection, trend structure analysis
- **Dynamic Symbol Support**: Auto-fetches all 782+ MEXC futures pairs with validation and fuzzy search
- **Advanced Signal Generation**: Multi-timeframe confluence with weighted scoring system
- **Machine Learning**: Optional ML-based signal generation using Random Forest with 6 features
- **Backtesting**: Comprehensive backtesting with performance metrics and trade analysis
- **Professional CLI**: Feature-rich command-line interface with symbol search and filtering

## Installation

1. **Clone or download the project files**

2. **Create and activate virtual environment**:
   ```bash
   python -m venv crypto-signal-tool/venv
   crypto-signal-tool/venv/Scripts/activate  # Windows
   # or
   source crypto-signal-tool/venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Signal Analysis
```bash
python cli.py --symbol BTC_USDT
```

### With Price Action Analysis
```bash
python cli.py --symbol BTC_USDT --price-action
```

### With Machine Learning
```bash
python cli.py --symbol BTC_USDT --ml --price-action
```

### Specific Indicator Categories
```bash
python cli.py --symbol ETH_USDT --indicators trend momentum volume
```

### Different Time Intervals
```bash
python cli.py --symbol SOL_USDT --interval Min5 --price-action
```

### Symbol Management
```bash
# List all available trading pairs
python cli.py --list-symbols

# Search for symbols
python cli.py --search btc
python cli.py --search doge
```

### Run Backtest
```bash
python cli.py --symbol BTC_USDT --backtest
```

### Available Options
- `--symbol`: Trading pair (auto-validates from 782+ MEXC futures pairs)
- `--interval`: Time interval (Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1)
- `--indicators`: Specify categories (trend, momentum, volume, volatility, oscillators)
- `--price-action`: Enable candlestick patterns and support/resistance analysis
- `--ml`: Enable machine learning signals
- `--backtest`: Run backtesting mode
- `--list-symbols`: Show all available trading pairs
- `--search`: Search for symbols with fuzzy matching
- `--verbose`: Verbose output

## Project Structure

```
├── cli.py              # Enhanced command-line interface with symbol management
├── config.py           # Configuration settings
├── data_fetcher.py     # MEXC API data fetching with interval support
├── indicators.py       # Comprehensive technical indicators + price action analysis
├── signal_generator.py # Advanced signal generation with weighted scoring
├── symbol_manager.py   # Dynamic symbol validation and fuzzy search
├── backtest.py         # Backtesting functionality with performance metrics
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Technical Indicators

### Trend Indicators
- **MACD (12, 26, 9)**: Moving Average Convergence Divergence
- **EMA (20, 50, 200)**: Exponential Moving Averages
- **Parabolic SAR**: Stop and Reverse trend indicator
- **ADX (14)**: Average Directional Index for trend strength
- **Ichimoku Cloud**: Complete trend analysis system

### Momentum Indicators
- **RSI (14)**: Relative Strength Index
- **Williams %R (14)**: Momentum oscillator
- **CCI (14)**: Commodity Channel Index
- **ROC**: Rate of Change
- **Stochastic Oscillator (14, 3, 3)**: Momentum indicator

### Volume Indicators
- **VWAP**: Volume Weighted Average Price
- **OBV**: On-Balance Volume
- **Volume ROC**: Volume Rate of Change
- **MFI (14)**: Money Flow Index

### Volatility Indicators
- **Bollinger Bands (20, 2)**: Price volatility bands
- **ATR**: Average True Range
- **Keltner Channels**: Volatility-based channels

### Oscillators
- **Ultimate Oscillator**: Multi-timeframe momentum oscillator

### Price Action Analysis
- **Candlestick Patterns**: Doji, Hammer, Shooting Star, Engulfing patterns
- **Support/Resistance**: Pivot point detection
- **Trend Structure**: Higher highs/lower lows analysis

## Signal Strategy

The system uses an advanced weighted confluence approach:

### Indicator Categories & Weights
- **Trend Indicators (30%)**: MACD, EMA, ADX, Parabolic SAR, Ichimoku
- **Momentum Indicators (25%)**: RSI, Williams %R, CCI, ROC, Stochastic
- **Volume Indicators (20%)**: VWAP, OBV, Volume ROC, MFI
- **Volatility Indicators (15%)**: Bollinger Bands, ATR, Keltner Channels
- **Price Action (10%)**: Candlestick patterns, Support/Resistance

### Signal Generation Process
1. **Multi-Indicator Scoring**: Each category contributes weighted scores
2. **Confluence Requirement**: Signals require multiple confirming indicators
3. **Strength Calculation**: Signal strength (0-1) based on total confluence
4. **Threshold Filtering**: Only signals above 1.5 threshold are generated
5. **Price Action Confirmation**: Optional candlestick pattern validation

### Signal Types
- **BUY**: Bullish confluence score > 1.5
- **SELL**: Bearish confluence score < -1.5
- **HOLD**: Neutral score between -1.5 and 1.5

## Machine Learning

The ML component uses a Random Forest classifier trained on:
- RSI values
- Price volatility
- EMA values
- Price changes
- Volume moving average

The model predicts future price direction based on current market conditions.

## Example Output

```
==================================================
TRADING SIGNAL ANALYSIS FOR BTC_USDT
==================================================
Latest Signal: HOLD
Signal Strength: 0.00
Signal Reason: 
Timestamp: 2025-06-02 21:45:00
Current Price: $104,804.80
RSI: 57.27
MACD: 133.3264

==================================================
RECENT SIGNALS:
==================================================
No recent signals found.

==================================================
LATEST DATA:
==================================================
                        close     RSI_14  MACD_12_26_9  signal  signal_strength
timestamp                                                                        
2025-06-02 21:15:00  104745.3  56.516119    133.326400       0              0.0
2025-06-02 21:30:00  104640.4  53.773131    133.326400       0              0.0
2025-06-02 21:45:00  104804.8  57.273098    133.326400       0              0.0
```

## Supported Trading Pairs

Any MEXC futures trading pair, including:
- BTC_USDT
- ETH_USDT
- And many others available on MEXC

## Disclaimer

This tool is for educational and research purposes only. Cryptocurrency trading involves significant risk, and you should never trade with money you cannot afford to lose. Always do your own research and consider consulting with a financial advisor before making trading decisions.

## Future Enhancements

- Real-time WebSocket data streaming
- More sophisticated ML models
- Portfolio management features
- Risk management tools
- Web-based dashboard
- Alert notifications
- More trading strategies
