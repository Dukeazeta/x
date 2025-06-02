import argparse
import sys
from data_fetcher import fetch_candles
from indicators import calculate_indicators
from signal_generator import generate_signals, ml_signal_generator, multi_timeframe_analysis, calculate_mtf_confluence
from backtest import simple_backtest, print_backtest_results
from symbol_manager import symbol_manager
from websocket_stream import MexcWebSocketStream, MultiSymbolStream, print_signal_callback
import time

def print_mtf_results(mtf_results, confluence):
    """Print formatted multi-timeframe analysis results"""

    print(f"\n{'='*60}")
    print("MULTI-TIMEFRAME CONFLUENCE ANALYSIS")
    print(f"{'='*60}")

    # Overall confluence
    final_signal = confluence['final_signal']
    confluence_score = confluence['confluence_score']
    signal_strength = confluence['signal_strength']
    trend_consensus = confluence['trend_consensus']
    trend_agreement = confluence['trend_agreement']

    print(f"🎯 FINAL SIGNAL: {final_signal}")
    print(f"📊 Confluence Score: {confluence_score:.3f}")
    print(f"💪 Signal Strength: {signal_strength:.3f}")
    print(f"📈 Trend Consensus: {trend_consensus}")
    print(f"🤝 Trend Agreement: {trend_agreement:.1%}")
    print(f"⏰ Timeframes Analyzed: {confluence['timeframes_analyzed']}")

    print(f"\n{'='*60}")
    print("TIMEFRAME BREAKDOWN")
    print(f"{'='*60}")

    # Timeframe details
    for timeframe, results in mtf_results.items():
        signal = 'BUY' if results['signal'] == 1 else 'SELL' if results['signal'] == -1 else 'HOLD'
        strength = results['signal_strength']
        trend = results['trend_structure']
        price = results['price']

        print(f"\n📅 {timeframe}:")
        print(f"   Signal: {signal} (Strength: {strength:.3f})")
        print(f"   Trend: {trend}")
        print(f"   Price: ${price:,.2f}")

        if results['rsi'] is not None:
            print(f"   RSI: {results['rsi']:.2f}")
        if results['macd'] is not None:
            print(f"   MACD: {results['macd']:.4f}")
        if results['adx'] is not None:
            print(f"   ADX: {results['adx']:.2f}")

        if results['support_level'] is not None:
            print(f"   Support: ${results['support_level']:,.2f}")
        if results['resistance_level'] is not None:
            print(f"   Resistance: ${results['resistance_level']:,.2f}")

    print(f"\n{'='*60}")
    print("SIGNAL CONTRIBUTIONS")
    print(f"{'='*60}")

    # Signal breakdown
    for timeframe, breakdown in confluence['signal_breakdown'].items():
        signal = breakdown['signal']
        weight = breakdown['weight']
        contribution = breakdown['contribution']

        print(f"{timeframe:<8}: {signal:<4} (Weight: {weight:.1f}, Contribution: {contribution:+.3f})")

    print(f"\n{'='*60}")
    print("TRADING RECOMMENDATION")
    print(f"{'='*60}")

    if final_signal == 'BUY':
        print("🟢 BULLISH CONFLUENCE DETECTED")
        print("   Consider LONG position with proper risk management")
    elif final_signal == 'SELL':
        print("🔴 BEARISH CONFLUENCE DETECTED")
        print("   Consider SHORT position with proper risk management")
    else:
        print("🟡 NEUTRAL/MIXED SIGNALS")
        print("   Wait for clearer confluence before entering position")

    print(f"\n⚠️  Always use proper risk management and position sizing!")

def main():
    parser = argparse.ArgumentParser(description='Crypto Trading Signal Generator')
    parser.add_argument('--symbol', type=str, default='BTC_USDT', help='Trading pair symbol')
    parser.add_argument('--ml', action='store_true', help='Use ML model for signals')
    parser.add_argument('--interval', type=str, default='Min15',
                       choices=['Min1', 'Min5', 'Min15', 'Min30', 'Min60', 'Hour4', 'Hour8', 'Day1'],
                       help='Time interval for data')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--backtest', action='store_true', help='Run backtest instead of live analysis')
    parser.add_argument('--list-symbols', action='store_true', help='List all available trading pairs')
    parser.add_argument('--price-action', action='store_true', help='Include price action analysis')
    parser.add_argument('--indicators', type=str, nargs='+',
                       choices=['trend', 'momentum', 'volume', 'volatility', 'oscillators'],
                       help='Specify which indicator categories to use')
    parser.add_argument('--search', type=str, help='Search for symbols matching the query')
    parser.add_argument('--mtf', '--multi-timeframe', action='store_true',
                       help='Enable multi-timeframe analysis')
    parser.add_argument('--timeframes', type=str, nargs='+',
                       default=['Min15', 'Min60', 'Hour4'],
                       choices=['Min1', 'Min5', 'Min15', 'Min30', 'Min60', 'Hour4', 'Hour8', 'Day1'],
                       help='Timeframes for MTF analysis (default: Min15 Min60 Hour4)')
    parser.add_argument('--stream', action='store_true',
                       help='Enable real-time WebSocket streaming')
    parser.add_argument('--stream-symbols', type=str, nargs='+',
                       help='Symbols to stream (default: uses --symbol)')

    args = parser.parse_args()

    # Handle list symbols request
    if args.list_symbols:
        print("Available MEXC Futures Trading Pairs:")
        print("=" * 50)
        popular_symbols = symbol_manager.get_popular_symbols(50)
        print(symbol_manager.format_symbol_list(popular_symbols, show_info=True))
        return

    # Handle symbol search
    if args.search:
        print(f"Searching for symbols matching '{args.search}':")
        print("=" * 50)
        matches = symbol_manager.fuzzy_search(args.search, max_results=10)
        if matches:
            print(symbol_manager.format_symbol_list(matches, show_info=True))
        else:
            print("No matching symbols found.")
        return

    # Validate and normalize symbol
    symbol, is_valid, message = symbol_manager.validate_symbol(args.symbol)
    if not is_valid:
        print(f"Error: {message}")
        # Try to suggest similar symbols
        suggestions = symbol_manager.fuzzy_search(args.symbol, max_results=5)
        if suggestions:
            print(f"Did you mean one of these?")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        sys.exit(1)

    args.symbol = symbol  # Use normalized symbol

    # Run backtest if requested
    if args.backtest:
        print("Running backtest mode...")
        results = simple_backtest(args.symbol)
        print_backtest_results(results)
        return

    # Run multi-timeframe analysis if requested
    if args.mtf:
        print(f"Running Multi-Timeframe Analysis for {args.symbol}")
        print(f"Timeframes: {', '.join(args.timeframes)}")
        print("=" * 60)

        # Perform MTF analysis
        mtf_results = multi_timeframe_analysis(
            args.symbol,
            timeframes=args.timeframes,
            use_price_action=args.price_action
        )

        if not mtf_results:
            print("No data available for multi-timeframe analysis")
            return

        # Calculate confluence
        confluence = calculate_mtf_confluence(mtf_results)

        # Display MTF results
        print_mtf_results(mtf_results, confluence)
        return

    # Run real-time streaming if requested
    if args.stream:
        symbols_to_stream = args.stream_symbols if args.stream_symbols else [args.symbol]

        print(f"🚀 Starting Real-Time Signal Monitoring")
        print(f"Symbols: {', '.join(symbols_to_stream)}")
        print(f"Interval: {args.interval}")
        print("=" * 60)
        print("Press Ctrl+C to stop streaming")
        print("=" * 60)

        # Create multi-symbol stream manager
        stream_manager = MultiSymbolStream()

        # Add enhanced callback for better output
        def enhanced_signal_callback(signal_data):
            timestamp = signal_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            symbol = signal_data['symbol']
            signal = signal_data['signal']
            strength = signal_data['signal_strength']
            price = signal_data['price']
            reason = signal_data['signal_reason']

            print(f"\n🚨 LIVE SIGNAL ALERT 🚨")
            print(f"Symbol: {symbol}")
            print(f"Signal: {signal}")
            print(f"Strength: {strength:.3f}")
            print(f"Price: ${price:,.2f}")
            print(f"Reason: {reason}")
            print(f"Time: {timestamp}")

            if signal_data['rsi'] is not None:
                print(f"RSI: {signal_data['rsi']:.2f}")
            if signal_data['macd'] is not None:
                print(f"MACD: {signal_data['macd']:.4f}")
            if signal_data['adx'] is not None:
                print(f"ADX: {signal_data['adx']:.2f}")

            print("-" * 60)

        stream_manager.add_global_callback(enhanced_signal_callback)

        # Add symbols to stream
        for symbol in symbols_to_stream:
            # Validate symbol
            normalized_symbol, is_valid, message = symbol_manager.validate_symbol(symbol)
            if not is_valid:
                print(f"⚠️  Skipping {symbol}: {message}")
                continue

            stream_manager.add_symbol(normalized_symbol, args.interval)

        try:
            # Start all streams
            threads = stream_manager.start_all_streams()

            if not threads:
                print("❌ No valid symbols to stream")
                return

            print(f"✅ Started streaming {len(threads)} symbols")
            print("Waiting for signals...")

            # Keep main thread alive
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping all streams...")
            stream_manager.stop_all_streams()
            print("✅ All streams stopped.")
            return

    print(f"Fetching data for {args.symbol} ({args.interval})...")
    df = fetch_candles(args.symbol, args.interval)
    
    if df is not None:
        print("Calculating indicators...")
        indicator_categories = args.indicators if args.indicators else None
        df = calculate_indicators(df, indicator_categories)

        print("Generating signals...")
        df = generate_signals(df, use_price_action=args.price_action)

        if args.ml:
            print("Generating ML signals...")
            df = ml_signal_generator(df)

        # Display results
        latest_row = df.iloc[-1]
        latest_signal = latest_row['signal']
        signal_strength = latest_row.get('signal_strength', 0)
        signal_reason = latest_row.get('signal_reason', 'N/A')

        action = "BUY" if latest_signal == 1 else "SELL" if latest_signal == -1 else "HOLD"

        print(f"\n{'='*50}")
        print(f"TRADING SIGNAL ANALYSIS FOR {args.symbol}")
        print(f"{'='*50}")
        print(f"Latest Signal: {action}")
        print(f"Signal Strength: {signal_strength:.2f}")
        print(f"Signal Reason: {signal_reason}")
        print(f"Timestamp: {df.index[-1]}")
        print(f"Current Price: ${latest_row['close']:,.2f}")

        # Show key indicators
        if 'RSI_14' in latest_row:
            print(f"RSI: {latest_row['RSI_14']:.2f}")
        if 'MACD_12_26_9' in latest_row:
            print(f"MACD: {latest_row['MACD_12_26_9']:.4f}")
        if 'ADX_14' in latest_row:
            print(f"ADX: {latest_row['ADX_14']:.2f}")
        if 'VWAP' in latest_row:
            print(f"VWAP: ${latest_row['VWAP']:,.2f}")

        # Show signal components if available
        signal_components = latest_row.get('signal_components', '')
        if signal_components:
            print(f"Signal Components: {signal_components}")

        # Show support/resistance if available
        if 'support_level' in latest_row and latest_row['support_level'] is not None:
            print(f"Support Level: ${latest_row['support_level']:,.2f}")
        if 'resistance_level' in latest_row and latest_row['resistance_level'] is not None:
            print(f"Resistance Level: ${latest_row['resistance_level']:,.2f}")

        # Show trend structure if available
        if 'trend_structure' in latest_row:
            print(f"Trend Structure: {latest_row['trend_structure']}")

        # Show candlestick patterns if price action is enabled
        if args.price_action:
            patterns = []
            if latest_row.get('doji', False):
                patterns.append('Doji')
            if latest_row.get('hammer', False):
                patterns.append('Hammer')
            if latest_row.get('shooting_star', False):
                patterns.append('Shooting Star')
            if latest_row.get('bullish_engulfing', False):
                patterns.append('Bullish Engulfing')
            if latest_row.get('bearish_engulfing', False):
                patterns.append('Bearish Engulfing')

            if patterns:
                print(f"Candlestick Patterns: {', '.join(patterns)}")

        print(f"\n{'='*50}")
        print("RECENT SIGNALS:")
        print(f"{'='*50}")

        # Show recent signals
        recent_signals = df[df['signal'] != 0].tail(5)
        if len(recent_signals) > 0:
            for idx, row in recent_signals.iterrows():
                sig_action = "BUY" if row['signal'] == 1 else "SELL"
                print(f"{idx}: {sig_action} (Strength: {row.get('signal_strength', 0):.2f}) - {row.get('signal_reason', 'N/A')}")
        else:
            print("No recent signals found.")

        print(f"\n{'='*50}")
        print("LATEST DATA:")
        print(f"{'='*50}")
        print(df[['close', 'RSI_14', 'MACD_12_26_9', 'signal', 'signal_strength']].tail(3))

if __name__ == "__main__":
    main()