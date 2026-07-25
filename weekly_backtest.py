#!/usr/bin/env python
"""Weekly Tuesday Buy/Sell Backtest for Top 5 Stocks (1 Year)"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json

# Top 5 from latest analysis
TOP5_TICKERS = ['KHC', 'PM', 'RTX', 'JPM', 'AAPL']

print("=" * 80)
print("WEEKLY BACKTEST: Buy Tuesday Open, Sell Next Tuesday Open (1 Year)")
print("=" * 80)

# Get 1 year of data (from 2025-07-25 to 2026-07-25)
end_date = datetime(2026, 7, 25)
start_date = end_date - timedelta(days=365)

print(f"\nPeriod: {start_date.date()} to {end_date.date()}\n")

# Collect all results
all_results = {}
total_trades = 0
total_profit_loss = 0.0
total_return_pct = 0.0
winning_trades = 0
losing_trades = 0

for ticker in TOP5_TICKERS:
    print(f"\n{'='*80}")
    print(f"TICKER: {ticker}")
    print(f"{'='*80}\n")

    try:
        # Download data
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty or len(df) < 10:
            print(f"  ERROR: Insufficient data for {ticker}")
            continue

        # Reset index to use Date as column
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df['DayOfWeek'] = df['Date'].dt.dayofweek  # 0=Monday, 1=Tuesday, ..., 4=Friday

        # Get all Tuesdays (dayofweek == 1)
        tuesdays = df[df['DayOfWeek'] == 1].copy()

        if len(tuesdays) < 2:
            print(f"  ERROR: Not enough Tuesdays for {ticker}")
            continue

        tuesdays = tuesdays.reset_index(drop=True)

        # Simulate weekly trades
        ticker_trades = []
        ticker_profit_loss = 0.0
        ticker_return_pct = 0.0
        ticker_wins = 0
        ticker_losses = 0

        for i in range(len(tuesdays) - 1):
            buy_date = tuesdays.iloc[i]['Date']
            buy_price = tuesdays.iloc[i]['Open']

            sell_date = tuesdays.iloc[i + 1]['Date']
            sell_price = tuesdays.iloc[i + 1]['Open']

            profit = sell_price - buy_price
            return_pct = (profit / buy_price) * 100

            ticker_trades.append({
                'week': i + 1,
                'buy_date': buy_date.strftime('%Y-%m-%d'),
                'buy_price': round(buy_price, 2),
                'sell_date': sell_date.strftime('%Y-%m-%d'),
                'sell_price': round(sell_price, 2),
                'profit_loss': round(profit, 2),
                'return_pct': round(return_pct, 2)
            })

            ticker_profit_loss += profit
            ticker_return_pct += return_pct

            if profit > 0:
                ticker_wins += 1
            elif profit < 0:
                ticker_losses += 0

            total_trades += 1
            total_profit_loss += profit

        ticker_avg_return = ticker_return_pct / len(ticker_trades) if ticker_trades else 0

        # Display results
        print(f"Total Trades: {len(ticker_trades)}")
        print(f"Winning Trades: {ticker_wins}")
        print(f"Losing Trades: {ticker_losses}")
        print(f"Total P&L: ${ticker_profit_loss:,.2f}")
        print(f"Total Return: {ticker_return_pct:.2f}%")
        print(f"Average Return/Trade: {ticker_avg_return:.2f}%")

        print(f"\nFirst 5 trades:")
        for trade in ticker_trades[:5]:
            print(f"  Week {trade['week']}: "
                  f"Buy ${trade['buy_price']:.2f} ({trade['buy_date']}) → "
                  f"Sell ${trade['sell_price']:.2f} ({trade['sell_date']}) | "
                  f"P&L: ${trade['profit_loss']:+.2f} ({trade['return_pct']:+.2f}%)")

        print(f"\nLast 5 trades:")
        for trade in ticker_trades[-5:]:
            print(f"  Week {trade['week']}: "
                  f"Buy ${trade['buy_price']:.2f} ({trade['buy_date']}) → "
                  f"Sell ${trade['sell_price']:.2f} ({trade['sell_date']}) | "
                  f"P&L: ${trade['profit_loss']:+.2f} ({trade['return_pct']:+.2f}%)")

        all_results[ticker] = {
            'trades': ticker_trades,
            'total_trades': len(ticker_trades),
            'winning_trades': ticker_wins,
            'losing_trades': ticker_losses,
            'total_pnl': round(ticker_profit_loss, 2),
            'total_return_pct': round(ticker_return_pct, 2),
            'avg_return_pct': round(ticker_avg_return, 2),
            'win_rate_pct': round((ticker_wins / len(ticker_trades) * 100) if ticker_trades else 0, 2)
        }

        total_profit_loss += 0  # Already added above
        winning_trades += ticker_wins
        losing_trades += ticker_losses

    except Exception as e:
        print(f"  ERROR: {e}")

# Summary statistics
print(f"\n{'='*80}")
print("AGGREGATE RESULTS (ALL 5 TICKERS)")
print(f"{'='*80}\n")

total_trades_count = sum(r['total_trades'] for r in all_results.values())
total_wins = sum(r['winning_trades'] for r in all_results.values())
total_losses = sum(r['losing_trades'] for r in all_results.values())
total_pnl_sum = sum(r['total_pnl'] for r in all_results.values())

print(f"Total Trades: {total_trades_count}")
print(f"Total Winning: {total_wins}")
print(f"Total Losing: {total_losses}")
print(f"Win Rate: {(total_wins / total_trades_count * 100) if total_trades_count > 0 else 0:.2f}%")
print(f"Total P&L: ${total_pnl_sum:,.2f}")
print(f"Average P&L per Trade: ${total_pnl_sum / total_trades_count if total_trades_count > 0 else 0:,.2f}")

# Per-ticker summary
print(f"\n{'Ticker':<10} {'Trades':<8} {'Wins':<8} {'Loss':<8} {'P&L':<12} {'Return%':<10} {'Avg%':<10} {'Win%':<10}")
print("-" * 80)

for ticker in TOP5_TICKERS:
    if ticker in all_results:
        r = all_results[ticker]
        print(f"{ticker:<10} {r['total_trades']:<8} {r['winning_trades']:<8} {r['losing_trades']:<8} "
              f"${r['total_pnl']:>10,.2f} {r['total_return_pct']:>9.2f}% {r['avg_return_pct']:>9.2f}% {r['win_rate_pct']:>9.2f}%")

# Save detailed results
output_file = 'outputs/weekly_backtest_results.json'
with open(output_file, 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\n✓ Detailed results saved to: {output_file}")
print("=" * 80)
