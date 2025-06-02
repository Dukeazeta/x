import numpy as np
from sklearn.ensemble import RandomForestClassifier
from indicators import detect_candlestick_patterns, detect_support_resistance, analyze_trend_structure
from data_fetcher import fetch_candles
from indicators import calculate_indicators

def generate_signals(df, use_price_action=True, indicator_weights=None):
    """
    Generate comprehensive trading signals

    Args:
        df: DataFrame with OHLCV data and indicators
        use_price_action: Whether to include price action analysis
        indicator_weights: Dict with weights for different indicator categories
    """
    # Create a copy to avoid warnings
    df = df.copy()

    # Default weights for different indicator categories
    if indicator_weights is None:
        indicator_weights = {
            'trend': 0.3,
            'momentum': 0.25,
            'volume': 0.2,
            'volatility': 0.15,
            'price_action': 0.1
        }

    # Initialize signals
    df['signal'] = 0  # 0 = hold, 1 = buy, -1 = sell
    df['signal_strength'] = 0.0  # Signal confidence (0-1)
    df['signal_reason'] = ''  # Reason for signal
    df['signal_components'] = ''  # Detailed breakdown

    # Add price action analysis if requested
    if use_price_action:
        df = detect_candlestick_patterns(df)
        df = detect_support_resistance(df)
        df = analyze_trend_structure(df)

    # Initialize signal scoring system
    signal_scores = np.zeros(len(df))
    signal_components = [''] * len(df)

    # TREND INDICATORS ANALYSIS
    trend_score = np.zeros(len(df))
    trend_components = []

    # MACD Analysis
    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
        macd_bullish = (df['MACD_12_26_9'] > df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift() <= df['MACDs_12_26_9'].shift())
        macd_bearish = (df['MACD_12_26_9'] < df['MACDs_12_26_9']) & (df['MACD_12_26_9'].shift() >= df['MACDs_12_26_9'].shift())
        trend_score += macd_bullish.astype(int) * 2 - macd_bearish.astype(int) * 2
        trend_components.append('MACD')

    # EMA Trend
    if 'EMA_20' in df.columns and 'EMA_50' in df.columns:
        ema_bullish = df['EMA_20'] > df['EMA_50']
        ema_bearish = df['EMA_20'] < df['EMA_50']
        trend_score += ema_bullish.astype(int) - ema_bearish.astype(int)
        trend_components.append('EMA')

    # ADX Trend Strength
    if 'ADX_14' in df.columns:
        strong_trend = df['ADX_14'] > 25
        trend_score += strong_trend.astype(int) * 0.5
        trend_components.append('ADX')

    # Parabolic SAR
    if 'PSARl_0.02_0.2' in df.columns and 'PSARs_0.02_0.2' in df.columns:
        psar_bullish = df['close'] > df['PSARl_0.02_0.2']
        psar_bearish = df['close'] < df['PSARs_0.02_0.2']
        trend_score += psar_bullish.astype(int) - psar_bearish.astype(int)
        trend_components.append('PSAR')

    # MOMENTUM INDICATORS ANALYSIS
    momentum_score = np.zeros(len(df))
    momentum_components = []

    # RSI Analysis
    if 'RSI_14' in df.columns:
        rsi_oversold = df['RSI_14'] < 30
        rsi_overbought = df['RSI_14'] > 70
        rsi_bullish = (df['RSI_14'] > 50) & (df['RSI_14'].shift() <= 50)
        rsi_bearish = (df['RSI_14'] < 50) & (df['RSI_14'].shift() >= 50)
        momentum_score += rsi_oversold.astype(int) * 2 - rsi_overbought.astype(int) * 2
        momentum_score += rsi_bullish.astype(int) - rsi_bearish.astype(int)
        momentum_components.append('RSI')

    # Williams %R
    if 'WILLR_14' in df.columns:
        willr_oversold = df['WILLR_14'] < -80
        willr_overbought = df['WILLR_14'] > -20
        momentum_score += willr_oversold.astype(int) - willr_overbought.astype(int)
        momentum_components.append('WILLR')

    # CCI Analysis
    if 'CCI_14_0.015' in df.columns:
        cci_oversold = df['CCI_14_0.015'] < -100
        cci_overbought = df['CCI_14_0.015'] > 100
        momentum_score += cci_oversold.astype(int) - cci_overbought.astype(int)
        momentum_components.append('CCI')

    # VOLUME INDICATORS ANALYSIS
    volume_score = np.zeros(len(df))
    volume_components = []

    # OBV Analysis
    if 'OBV' in df.columns:
        obv_rising = df['OBV'] > df['OBV'].shift(5)
        obv_falling = df['OBV'] < df['OBV'].shift(5)
        volume_score += obv_rising.astype(int) - obv_falling.astype(int)
        volume_components.append('OBV')

    # MFI Analysis
    if 'MFI_14' in df.columns:
        mfi_oversold = df['MFI_14'] < 20
        mfi_overbought = df['MFI_14'] > 80
        volume_score += mfi_oversold.astype(int) - mfi_overbought.astype(int)
        volume_components.append('MFI')

    # VOLATILITY INDICATORS ANALYSIS
    volatility_score = np.zeros(len(df))
    volatility_components = []

    # Bollinger Bands
    bb_lower_col = next((col for col in df.columns if col.startswith('BBL_')), None)
    bb_upper_col = next((col for col in df.columns if col.startswith('BBU_')), None)

    if bb_lower_col and bb_upper_col:
        bb_oversold = df['close'] < df[bb_lower_col]
        bb_overbought = df['close'] > df[bb_upper_col]
        volatility_score += bb_oversold.astype(int) - bb_overbought.astype(int)
        volatility_components.append('BB')

    # Keltner Channels
    if 'KCLe_20_2' in df.columns and 'KCUe_20_2' in df.columns:
        kc_oversold = df['close'] < df['KCLe_20_2']
        kc_overbought = df['close'] > df['KCUe_20_2']
        volatility_score += kc_oversold.astype(int) - kc_overbought.astype(int)
        volatility_components.append('KC')

    # PRICE ACTION ANALYSIS
    price_action_score = np.zeros(len(df))
    price_action_components = []

    if use_price_action:
        # Candlestick patterns
        if 'bullish_engulfing' in df.columns:
            price_action_score += df['bullish_engulfing'].astype(int) * 2
            price_action_components.append('Bullish_Engulfing')

        if 'bearish_engulfing' in df.columns:
            price_action_score -= df['bearish_engulfing'].astype(int) * 2
            price_action_components.append('Bearish_Engulfing')

        if 'hammer' in df.columns:
            price_action_score += df['hammer'].astype(int)
            price_action_components.append('Hammer')

        if 'shooting_star' in df.columns:
            price_action_score -= df['shooting_star'].astype(int)
            price_action_components.append('Shooting_Star')

    # COMBINE ALL SCORES WITH WEIGHTS
    final_score = (
        trend_score * indicator_weights.get('trend', 0.3) +
        momentum_score * indicator_weights.get('momentum', 0.25) +
        volume_score * indicator_weights.get('volume', 0.2) +
        volatility_score * indicator_weights.get('volatility', 0.15) +
        price_action_score * indicator_weights.get('price_action', 0.1)
    )

    # Generate signals based on combined score
    signal_threshold = 1.5
    df['signal'] = np.where(final_score > signal_threshold, 1,
                           np.where(final_score < -signal_threshold, -1, 0))

    # Calculate signal strength (0-1)
    max_possible_score = 10  # Approximate maximum possible score
    df['signal_strength'] = np.abs(final_score) / max_possible_score
    df['signal_strength'] = np.clip(df['signal_strength'], 0, 1)

    # Generate signal reasons
    for i in range(len(df)):
        components = []
        if trend_score[i] != 0:
            components.extend([f"{comp}({trend_score[i]:.1f})" for comp in trend_components])
        if momentum_score[i] != 0:
            components.extend([f"{comp}({momentum_score[i]:.1f})" for comp in momentum_components])
        if volume_score[i] != 0:
            components.extend([f"{comp}({volume_score[i]:.1f})" for comp in volume_components])
        if volatility_score[i] != 0:
            components.extend([f"{comp}({volatility_score[i]:.1f})" for comp in volatility_components])
        if use_price_action and price_action_score[i] != 0:
            components.extend([f"{comp}({price_action_score[i]:.1f})" for comp in price_action_components])

        df.loc[df.index[i], 'signal_components'] = ', '.join(components)

        if df.iloc[i]['signal'] == 1:
            df.loc[df.index[i], 'signal_reason'] = f"Bullish confluence (Score: {final_score[i]:.2f})"
        elif df.iloc[i]['signal'] == -1:
            df.loc[df.index[i], 'signal_reason'] = f"Bearish confluence (Score: {final_score[i]:.2f})"
        else:
            df.loc[df.index[i], 'signal_reason'] = f"Neutral (Score: {final_score[i]:.2f})"

    return df

def ml_signal_generator(df):
    """Machine learning signal generator"""
    # Create a copy to avoid warnings
    df = df.copy()

    # Feature engineering
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(20).std()
    df['price_change'] = df['close'].diff()
    df['volume_sma'] = df['volume'].rolling(20).mean()

    # Prepare features for ML
    feature_columns = ['RSI_14', 'volatility', 'EMA_20', 'EMA_50', 'price_change', 'volume_sma']
    available_features = [col for col in feature_columns if col in df.columns]

    if len(available_features) < 3:
        print("Warning: Not enough features for ML model. Skipping ML signals.")
        df['ml_signal'] = 0
        return df

    # Create target variable (future price direction)
    df['future_return'] = df['returns'].shift(-1)
    df['target'] = np.where(df['future_return'] > 0, 1, 0)

    # Prepare data for ML
    features_df = df[available_features].dropna()
    target_series = df.loc[features_df.index, 'target']

    # Need enough data for training
    if len(features_df) < 100:
        print("Warning: Not enough data for ML model. Skipping ML signals.")
        df['ml_signal'] = 0
        return df

    try:
        # Split data for training (use 80% for training)
        split_idx = int(len(features_df) * 0.8)
        X_train = features_df.iloc[:split_idx]
        y_train = target_series.iloc[:split_idx]

        # Train model
        model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        model.fit(X_train, y_train)

        # Predict signals for all data
        df['ml_signal'] = 0
        predictions = model.predict(features_df)
        df.loc[features_df.index, 'ml_signal'] = predictions

        # Convert to trading signals (-1, 0, 1)
        df['ml_signal'] = df['ml_signal'].map({0: -1, 1: 1})

        print(f"ML model trained with {len(X_train)} samples using features: {available_features}")

    except Exception as e:
        print(f"Error in ML model: {str(e)}")
        df['ml_signal'] = 0

    return df

def multi_timeframe_analysis(symbol, timeframes=['Min15', 'Hour1', 'Hour4'], use_price_action=True):
    """
    Perform multi-timeframe analysis for enhanced signal confirmation

    Args:
        symbol: Trading pair symbol
        timeframes: List of timeframes to analyze (ordered from shortest to longest)
        use_price_action: Whether to include price action analysis

    Returns:
        dict: MTF analysis results with signals for each timeframe
    """
    mtf_results = {}

    for timeframe in timeframes:
        print(f"Analyzing {timeframe} timeframe...")

        # Fetch data for this timeframe
        df = fetch_candles(symbol, timeframe)
        if df is None or len(df) < 50:
            print(f"Insufficient data for {timeframe}")
            continue

        # Calculate indicators
        df = calculate_indicators(df)

        # Generate signals
        df = generate_signals(df, use_price_action=use_price_action)

        # Extract key metrics
        latest_row = df.iloc[-1]

        mtf_results[timeframe] = {
            'signal': latest_row['signal'],
            'signal_strength': latest_row['signal_strength'],
            'signal_reason': latest_row['signal_reason'],
            'trend_structure': latest_row.get('trend_structure', 'unknown'),
            'rsi': latest_row.get('RSI_14', None),
            'macd': latest_row.get('MACD_12_26_9', None),
            'adx': latest_row.get('ADX_14', None),
            'price': latest_row['close'],
            'timestamp': df.index[-1],
            'support_level': latest_row.get('support_level', None),
            'resistance_level': latest_row.get('resistance_level', None)
        }

    return mtf_results

def calculate_mtf_confluence(mtf_results, timeframe_weights=None):
    """
    Calculate multi-timeframe confluence score

    Args:
        mtf_results: Results from multi_timeframe_analysis
        timeframe_weights: Dict with weights for each timeframe

    Returns:
        dict: Confluence analysis results
    """
    if timeframe_weights is None:
        # Default weights: longer timeframes have more weight
        timeframe_weights = {
            'Min1': 0.1,
            'Min5': 0.15,
            'Min15': 0.2,
            'Min30': 0.25,
            'Min60': 0.3,
            'Hour4': 0.5,
            'Hour8': 0.6,
            'Day1': 0.7
        }

    total_score = 0
    total_weight = 0
    signal_breakdown = {}
    trend_alignment = {}

    for timeframe, results in mtf_results.items():
        weight = timeframe_weights.get(timeframe, 0.1)
        signal = results['signal']
        strength = results['signal_strength']
        trend = results['trend_structure']

        # Calculate weighted signal contribution
        weighted_signal = signal * strength * weight
        total_score += weighted_signal
        total_weight += weight

        signal_breakdown[timeframe] = {
            'signal': 'BUY' if signal == 1 else 'SELL' if signal == -1 else 'HOLD',
            'strength': strength,
            'trend': trend,
            'weight': weight,
            'contribution': weighted_signal
        }

        trend_alignment[timeframe] = trend

    # Calculate final confluence score
    if total_weight > 0:
        confluence_score = total_score / total_weight
    else:
        confluence_score = 0

    # Determine final signal based on confluence
    if confluence_score > 0.3:
        final_signal = 'BUY'
    elif confluence_score < -0.3:
        final_signal = 'SELL'
    else:
        final_signal = 'HOLD'

    # Check trend alignment across timeframes
    trends = list(trend_alignment.values())
    trend_consensus = max(set(trends), key=trends.count) if trends else 'unknown'
    trend_agreement = trends.count(trend_consensus) / len(trends) if trends else 0

    return {
        'final_signal': final_signal,
        'confluence_score': confluence_score,
        'signal_strength': abs(confluence_score),
        'signal_breakdown': signal_breakdown,
        'trend_consensus': trend_consensus,
        'trend_agreement': trend_agreement,
        'timeframes_analyzed': len(mtf_results)
    }