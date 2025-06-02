import pandas_ta as ta
import numpy as np
import pandas as pd

def calculate_indicators(df, indicator_categories=None):
    """
    Calculate comprehensive technical indicators

    Args:
        df: DataFrame with OHLCV data
        indicator_categories: List of categories to calculate ['trend', 'momentum', 'volume', 'volatility', 'oscillators']
                             If None, calculates all categories
    """
    if indicator_categories is None:
        indicator_categories = ['trend', 'momentum', 'volume', 'volatility', 'oscillators']

    # Trend Indicators
    if 'trend' in indicator_categories:
        # Moving Averages
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.sma(length=200, append=True)

        # MACD
        df.ta.macd(append=True)

        # Parabolic SAR
        df.ta.psar(append=True)

        # Average Directional Index (ADX)
        df.ta.adx(append=True)

        # Ichimoku Cloud
        df.ta.ichimoku(append=True)

    # Momentum Indicators
    if 'momentum' in indicator_categories:
        # RSI
        df.ta.rsi(append=True)

        # Williams %R
        df.ta.willr(append=True)

        # Commodity Channel Index (CCI)
        df.ta.cci(append=True)

        # Rate of Change (ROC)
        df.ta.roc(append=True)

        # Stochastic Oscillator
        df.ta.stoch(append=True)

    # Volume Indicators
    if 'volume' in indicator_categories:
        # Volume Weighted Average Price (VWAP)
        df.ta.vwap(append=True)

        # On-Balance Volume (OBV)
        df.ta.obv(append=True)

        # Volume Rate of Change
        df.ta.roc(close=df['volume'], append=True, suffix='_vol')

        # Money Flow Index (MFI)
        df.ta.mfi(append=True)

    # Volatility Indicators
    if 'volatility' in indicator_categories:
        # Bollinger Bands
        df.ta.bbands(append=True)

        # Average True Range (ATR)
        df.ta.atr(append=True)

        # Keltner Channels
        df.ta.kc(append=True)

    # Oscillators
    if 'oscillators' in indicator_categories:
        # Ultimate Oscillator
        df.ta.uo(append=True)

        # Additional oscillators already covered in momentum
        pass

    # Only drop rows where essential indicators are missing
    essential_columns = ['close', 'open', 'high', 'low', 'volume']

    # Only drop rows where ALL essential data is missing
    return df.dropna(subset=essential_columns, how='all')

def detect_candlestick_patterns(df):
    """
    Detect common candlestick patterns
    """
    df = df.copy()

    # Calculate body and shadow sizes
    df['body_size'] = abs(df['close'] - df['open'])
    df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['total_range'] = df['high'] - df['low']

    # Doji pattern (small body relative to range)
    df['doji'] = (df['body_size'] / df['total_range'] < 0.1) & (df['total_range'] > 0)

    # Hammer pattern (small body, long lower shadow, small upper shadow)
    df['hammer'] = (
        (df['body_size'] / df['total_range'] < 0.3) &
        (df['lower_shadow'] > 2 * df['body_size']) &
        (df['upper_shadow'] < df['body_size'])
    )

    # Shooting Star (small body, long upper shadow, small lower shadow)
    df['shooting_star'] = (
        (df['body_size'] / df['total_range'] < 0.3) &
        (df['upper_shadow'] > 2 * df['body_size']) &
        (df['lower_shadow'] < df['body_size'])
    )

    # Engulfing patterns
    df['bullish_engulfing'] = (
        (df['close'] > df['open']) &  # Current candle is bullish
        (df['close'].shift(1) < df['open'].shift(1)) &  # Previous candle is bearish
        (df['open'] < df['close'].shift(1)) &  # Current open below previous close
        (df['close'] > df['open'].shift(1))  # Current close above previous open
    )

    df['bearish_engulfing'] = (
        (df['close'] < df['open']) &  # Current candle is bearish
        (df['close'].shift(1) > df['open'].shift(1)) &  # Previous candle is bullish
        (df['open'] > df['close'].shift(1)) &  # Current open above previous close
        (df['close'] < df['open'].shift(1))  # Current close below previous open
    )

    return df

def detect_support_resistance(df, window=20, min_touches=2):
    """
    Detect support and resistance levels using pivot points
    """
    df = df.copy()

    # Check if we have enough data
    if len(df) < window * 2:
        df['support_level'] = None
        df['resistance_level'] = None
        return df

    # Calculate pivot points
    df['pivot_high'] = df['high'].rolling(window=window, center=True).max() == df['high']
    df['pivot_low'] = df['low'].rolling(window=window, center=True).min() == df['low']

    # Get significant levels
    resistance_levels = df[df['pivot_high']]['high'].values
    support_levels = df[df['pivot_low']]['low'].values

    # Find current support and resistance
    if len(df) == 0:
        df['support_level'] = None
        df['resistance_level'] = None
        return df

    current_price = df['close'].iloc[-1]

    # Resistance: lowest high above current price
    resistance = None
    if len(resistance_levels) > 0:
        above_current = resistance_levels[resistance_levels > current_price]
        if len(above_current) > 0:
            resistance = above_current.min()

    # Support: highest low below current price
    support = None
    if len(support_levels) > 0:
        below_current = support_levels[support_levels < current_price]
        if len(below_current) > 0:
            support = below_current.max()

    df['support_level'] = support
    df['resistance_level'] = resistance

    return df

def analyze_trend_structure(df, lookback=50):
    """
    Analyze trend structure (higher highs/lower lows)
    """
    df = df.copy()

    # Check if we have enough data
    if len(df) < lookback:
        df['trend_structure'] = 'insufficient_data'
        return df

    # Calculate recent highs and lows
    recent_data = df.tail(lookback)

    # Find swing highs and lows
    swing_highs = []
    swing_lows = []

    # Need at least 11 data points for swing analysis
    if len(recent_data) < 11:
        df['trend_structure'] = 'insufficient_data'
        return df

    for i in range(5, len(recent_data) - 5):
        # Check if it's a swing high
        if (recent_data.iloc[i]['high'] > recent_data.iloc[i-5:i]['high'].max() and
            recent_data.iloc[i]['high'] > recent_data.iloc[i+1:i+6]['high'].max()):
            swing_highs.append(recent_data.iloc[i]['high'])

        # Check if it's a swing low
        if (recent_data.iloc[i]['low'] < recent_data.iloc[i-5:i]['low'].min() and
            recent_data.iloc[i]['low'] < recent_data.iloc[i+1:i+6]['low'].min()):
            swing_lows.append(recent_data.iloc[i]['low'])

    # Determine trend
    trend = 'sideways'
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
            trend = 'uptrend'
        elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
            trend = 'downtrend'

    df['trend_structure'] = trend

    return df