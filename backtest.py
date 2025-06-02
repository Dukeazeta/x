import pandas as pd
import numpy as np
from data_fetcher import fetch_candles
from indicators import calculate_indicators
from signal_generator import generate_signals

def simple_backtest(symbol, initial_balance=10000, transaction_fee=0.001):
    """
    Simple backtesting function for the trading strategy
    """
    print(f"Running backtest for {symbol}...")
    
    # Fetch data and generate signals
    df = fetch_candles(symbol)
    if df is None:
        print("Failed to fetch data")
        return None
    
    df = calculate_indicators(df)
    df = generate_signals(df)
    
    # Initialize backtest variables
    balance = initial_balance
    position = 0  # 0 = no position, 1 = long, -1 = short
    entry_price = 0
    trades = []
    portfolio_value = []
    
    for i, (timestamp, row) in enumerate(df.iterrows()):
        current_price = row['close']
        signal = row['signal']
        
        # Calculate current portfolio value
        if position == 0:
            current_value = balance
        elif position == 1:  # Long position
            current_value = balance * (current_price / entry_price)
        else:  # Short position
            current_value = balance * (2 - current_price / entry_price)
        
        portfolio_value.append(current_value)
        
        # Execute trades based on signals
        if signal == 1 and position <= 0:  # Buy signal
            if position == -1:  # Close short position
                pnl = balance * (2 - current_price / entry_price) - balance
                balance = balance + pnl
                trades.append({
                    'timestamp': timestamp,
                    'action': 'close_short',
                    'price': current_price,
                    'pnl': pnl,
                    'balance': balance
                })
            
            # Open long position
            entry_price = current_price * (1 + transaction_fee)
            position = 1
            trades.append({
                'timestamp': timestamp,
                'action': 'buy',
                'price': current_price,
                'pnl': 0,
                'balance': balance
            })
            
        elif signal == -1 and position >= 0:  # Sell signal
            if position == 1:  # Close long position
                pnl = balance * (current_price / entry_price) - balance
                balance = balance + pnl
                trades.append({
                    'timestamp': timestamp,
                    'action': 'close_long',
                    'price': current_price,
                    'pnl': pnl,
                    'balance': balance
                })
            
            # Open short position
            entry_price = current_price * (1 - transaction_fee)
            position = -1
            trades.append({
                'timestamp': timestamp,
                'action': 'sell',
                'price': current_price,
                'pnl': 0,
                'balance': balance
            })
    
    # Close any remaining position
    if position != 0:
        final_price = df.iloc[-1]['close']
        if position == 1:
            pnl = balance * (final_price / entry_price) - balance
        else:
            pnl = balance * (2 - final_price / entry_price) - balance
        balance = balance + pnl
        trades.append({
            'timestamp': df.index[-1],
            'action': 'close_final',
            'price': final_price,
            'pnl': pnl,
            'balance': balance
        })
    
    # Calculate performance metrics
    final_balance = balance
    total_return = (final_balance - initial_balance) / initial_balance * 100
    
    # Calculate max drawdown
    portfolio_series = pd.Series(portfolio_value, index=df.index)
    rolling_max = portfolio_series.expanding().max()
    drawdown = (portfolio_series - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    # Calculate win rate
    profitable_trades = [t for t in trades if t['pnl'] > 0]
    total_trades = len([t for t in trades if t['pnl'] != 0])
    win_rate = len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0
    
    results = {
        'initial_balance': initial_balance,
        'final_balance': final_balance,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'trades': trades,
        'portfolio_value': portfolio_series
    }
    
    return results

def print_backtest_results(results):
    """Print formatted backtest results"""
    if results is None:
        return
    
    print(f"\n{'='*50}")
    print("BACKTEST RESULTS")
    print(f"{'='*50}")
    print(f"Initial Balance: ${results['initial_balance']:,.2f}")
    print(f"Final Balance: ${results['final_balance']:,.2f}")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    
    print(f"\n{'='*50}")
    print("RECENT TRADES:")
    print(f"{'='*50}")
    for trade in results['trades'][-5:]:
        print(f"{trade['timestamp']}: {trade['action']} at ${trade['price']:.2f} "
              f"(PnL: ${trade['pnl']:.2f}, Balance: ${trade['balance']:.2f})")

if __name__ == "__main__":
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTC_USDT'
    results = simple_backtest(symbol)
    print_backtest_results(results)
