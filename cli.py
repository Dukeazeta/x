import argparse
import sys
from data_fetcher import fetch_candles
from indicators import calculate_indicators
from signal_generator import generate_signals, ml_signal_generator
from backtest import simple_backtest, print_backtest_results
from symbol_manager import symbol_manager

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