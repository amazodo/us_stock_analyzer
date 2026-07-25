#!/usr/bin/env python
"""
Weekly Top5 Stock Selection & Backtest (1 Year)
- Every Tuesday: Select Top5 using Technical Analysis only (no sentiment)
- Buy at Tuesday Open, Sell at Next Tuesday Open
- Analyze weekly & aggregate performance
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

# S&P 100 universe (excluding delisted)
STOCK_UNIVERSE = [
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA', 'META', 'BRK.A', 'JNJ', 'V',
    'WMT', 'JPM', 'PG', 'ABBV', 'XOM', 'AVGO', 'KO', 'PFE', 'COST', 'ACN',
    'CRM', 'LLY', 'MRK', 'NVO', 'NFLX', 'AMD', 'ADBE', 'AXP', 'MCD', 'PEP',
    'INTU', 'SBUX', 'HO', 'PEP', 'COP', 'CSCO', 'CVX', 'GE', 'BA', 'QCOM',
    'ISRG', 'TJX', 'CMG', 'PYPL', 'NOW', 'GILD', 'RTX', 'CAT', 'IBM', 'ARM',
    'ELV', 'MAR', 'PM', 'RELX', 'KKR', 'TMUS', 'LMT', 'DIS', 'BX', 'KLAC',
    'MU', 'SNPS', 'CDNS', 'DASH', 'COIN', 'UBER', 'CHWY', 'KMX', 'WDAY', 'ANET',
    'MAA', 'FANG', 'ROP', 'REGN', 'BDX', 'APD', 'OKE', 'PSA', 'MKTX', 'SMCI',
    'KHC', 'SLB', 'AEP', 'PCAR', 'PSTG', 'HPE', 'ULTA', 'VRSN', 'DHR', 'DUK'
]

print("=" * 100)
print("WEEKLY TOP5 BACKTEST: Technical Analysis Only (No Sentiment)")
print("=" * 100)

# Analysis period: 1 year
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

print(f"\nAnalysis Period: {start_date.date()} to {end_date.date()}\n")

# Download all stock data at once
# Need extra history for proper MA calculation (200 SMA)
print("Downloading historical data...")
all_data = {}
failed_tickers = []
download_start = start_date - timedelta(days=250)  # 250 days of extra history

for ticker in STOCK_UNIVERSE:
    try:
        df = yf.download(ticker, start=download_start, end=end_date, progress=False)
        if not df.empty and len(df) >= 60:
            # yfinance can return MultiIndex for single ticker, normalize to simple columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)  # Remove ticker level
            all_data[ticker] = df
        else:
            failed_tickers.append(f"{ticker}(len={len(df) if not df.empty else 0})")
    except Exception as e:
        failed_tickers.append(f"{ticker}(error)")

print(f"✓ Downloaded data for {len(all_data)} stocks")
if failed_tickers[:5]:
    print(f"  Failed: {', '.join(failed_tickers[:5])}")
print()

# Find all Tuesdays in the period
all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
tuesdays = [d for d in all_dates if d.dayofweek == 1]  # 1 = Tuesday

print(f"Total Tuesdays in period: {len(tuesdays)}\n")

# Function to calculate technical score (no sentiment)
def calculate_technical_score(df, ticker):
    """Simple technical analysis score based on price momentum & trend"""
    try:
        if len(df) < 60:
            return 50.0

        close = df['Close']

        # Trend scores
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else sma50

        price = close.iloc[-1]

        score = 50.0

        # Price vs moving averages
        if price > sma20:
            score += 10
        if price > sma50:
            score += 10
        if price > sma200:
            score += 10

        # MA alignment
        if sma20 > sma50 > sma200:
            score += 10

        # Momentum (30-day return)
        momentum = (close.iloc[-1] - close.iloc[-30]) / close.iloc[-30] * 100
        if momentum > 5:
            score += 10
        elif momentum > 0:
            score += 5
        elif momentum < -5:
            score -= 10

        # Volatility (lower volatility = better)
        volatility = close.pct_change().std() * 100
        if volatility < 2:
            score += 5

        return min(100, max(0, score))
    except:
        return 50.0

# Backtest: weekly selection and trading
weekly_results = []
portfolio_performance = []
all_trades = []

print(f"Starting backtest with {len(all_data)} stocks and {len(tuesdays)-1} trading weeks...\n")

# Debug: Check first Tuesday
if tuesdays:
    first_tuesday = tuesdays[0]
    print(f"First Tuesday: {first_tuesday.date()}")
    sample_ticker = [t for t in STOCK_UNIVERSE if t in all_data][0] if [t for t in STOCK_UNIVERSE if t in all_data] else None
    if sample_ticker:
        df_sample = all_data[sample_ticker]
        print(f"Sample ticker {sample_ticker}: index range {df_sample.index[0].date()} to {df_sample.index[-1].date()}, len={len(df_sample)}")
        df_subset = df_sample[df_sample.index.date <= first_tuesday.date()]
        print(f"Data up to first Tuesday: len={len(df_subset)}\n")

for week_idx, tuesday_date in enumerate(tuesdays[:-1]):  # -1 because we need next Tuesday
    next_tuesday = tuesdays[week_idx + 1]

    # Get data up to this Tuesday
    portfolio_scores = {}

    for ticker in STOCK_UNIVERSE:
        if ticker not in all_data:
            continue

        df = all_data[ticker]

        # Get data up to current Tuesday
        df_to_date = df[df.index.date <= tuesday_date.date()]

        if len(df_to_date) >= 60:
            score = calculate_technical_score(df_to_date, ticker)
            portfolio_scores[ticker] = score

    if not portfolio_scores:
        if week_idx < 3:
            print(f"  Week {week_idx+1} ({tuesday_date.date()}): No scorable stocks (need 60 days history)")
        continue

    # Select Top 5
    top5 = sorted(portfolio_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_tickers = [t[0] for t in top5]

    if week_idx == 0:
        print(f"Week 1 Top5: {top5_tickers} with scores {[round(s, 1) for _, s in top5]}")

    # Execute trades
    week_trades = []
    week_pnl = 0.0
    week_returns = 0.0

    for ticker in top5_tickers:
        try:
            # Get buy price (Tuesday open) - get last trading day on or before this Tuesday
            buy_data = all_data[ticker][all_data[ticker].index.date <= tuesday_date.date()]
            if buy_data.empty:
                if week_idx == 0:
                    print(f"    {ticker}: No buy_data before {tuesday_date.date()}")
                continue

            buy_date = buy_data.index[-1]
            buy_price = float(buy_data['Open'].iloc[-1])

            if week_idx == 0:
                print(f"    {ticker}: buy {buy_price} on {buy_date.date()}")

            # Get sell price (exactly next Tuesday's open)
            sell_data = all_data[ticker][all_data[ticker].index.date == next_tuesday.date()]

            if sell_data.empty:
                if week_idx == 0:
                    print(f"    {ticker}: No data on next Tuesday {next_tuesday.date()}")
                continue

            sell_date = sell_data.index[0]
            sell_price = float(sell_data['Open'].iloc[0])

            profit = sell_price - buy_price
            return_pct = (profit / buy_price) * 100

            week_trades.append({
                'ticker': ticker,
                'score': portfolio_scores[ticker],
                'buy_date': buy_date.strftime('%Y-%m-%d'),
                'buy_price': round(buy_price, 2),
                'sell_date': sell_date.strftime('%Y-%m-%d'),
                'sell_price': round(sell_price, 2),
                'profit_loss': round(profit, 2),
                'return_pct': round(return_pct, 2)
            })

            week_pnl += profit
            week_returns += return_pct

            all_trades.append({
                'week': week_idx + 1,
                'week_start': tuesday_date.strftime('%Y-%m-%d'),
                'ticker': ticker,
                'buy_price': round(buy_price, 2),
                'sell_price': round(sell_price, 2),
                'profit_loss': round(profit, 2),
                'return_pct': round(return_pct, 2)
            })

        except Exception as e:
            continue

    if week_trades:
        week_avg_return = week_returns / len(week_trades)
        wins = sum(1 for t in week_trades if t['return_pct'] > 0)

        weekly_result = {
            'week': week_idx + 1,
            'week_start': tuesday_date.strftime('%Y-%m-%d'),
            'week_end': next_tuesday.strftime('%Y-%m-%d'),
            'top5': top5_tickers,
            'trades': week_trades,
            'total_trades': len(week_trades),
            'winning_trades': wins,
            'losing_trades': len(week_trades) - wins,
            'total_pnl': round(week_pnl, 2),
            'total_return_pct': round(week_returns, 2),
            'avg_return_pct': round(week_avg_return, 2),
            'win_rate_pct': round((wins / len(week_trades) * 100) if week_trades else 0, 2)
        }

        weekly_results.append(weekly_result)
        portfolio_performance.append({
            'week': week_idx + 1,
            'pnl': round(week_pnl, 2),
            'return_pct': round(week_avg_return, 2)
        })

# Print results
print("\n" + "=" * 100)
print("WEEKLY RESULTS SUMMARY")
print("=" * 100 + "\n")

print(f"{'Week':<6} {'Start Date':<12} {'Top5':<30} {'Trades':<8} {'Wins':<6} {'P&L':<12} {'Avg%':<8} {'Win%':<8}")
print("-" * 100)

total_trades_all = 0
total_pnl_all = 0.0
total_wins_all = 0

for wr in weekly_results[:10]:  # First 10 weeks
    top5_str = ', '.join(wr['top5'])[:28]
    print(f"{wr['week']:<6} {wr['week_start']:<12} {top5_str:<30} {wr['total_trades']:<8} "
          f"{wr['winning_trades']:<6} ${wr['total_pnl']:>10,.2f} {wr['avg_return_pct']:>7.2f}% {wr['win_rate_pct']:>7.2f}%")

    total_trades_all += wr['total_trades']
    total_pnl_all += wr['total_pnl']
    total_wins_all += wr['winning_trades']

if len(weekly_results) > 10:
    print(f"... ({len(weekly_results) - 10} more weeks)")

# Aggregate statistics
print("\n" + "=" * 100)
print("AGGREGATE STATISTICS (ALL WEEKS)")
print("=" * 100 + "\n")

total_trades = sum(w['total_trades'] for w in weekly_results)
total_wins = sum(w['winning_trades'] for w in weekly_results)
total_losses = sum(w['losing_trades'] for w in weekly_results)
total_pnl = sum(w['total_pnl'] for w in weekly_results)
avg_return = sum(w['avg_return_pct'] for w in weekly_results) / len(weekly_results) if weekly_results else 0

if total_trades == 0:
    print("\n⚠️  WARNING: No trades executed. Check data download and date ranges.")
    print(f"   Weeks found: {len(tuesdays)}")
    print(f"   Data available for {len(all_data)} stocks")
    print(f"   Date range: {start_date.date()} to {end_date.date()}")
    import sys
    sys.exit(1)

print(f"Total Weeks Analyzed: {len(weekly_results)}")
print(f"Total Trades Executed: {total_trades}")
print(f"Winning Trades: {total_wins} ({(total_wins/total_trades*100) if total_trades > 0 else 0:.2f}%)")
print(f"Losing Trades: {total_losses} ({(total_losses/total_trades*100) if total_trades > 0 else 0:.2f}%)")
print(f"\nTotal P&L: ${total_pnl:,.2f}")
print(f"Average P&L per Trade: ${total_pnl/total_trades if total_trades > 0 else 0:,.2f}")
print(f"Average Weekly Return: {avg_return:.2f}%")
print(f"Cumulative Return: {sum(p['return_pct'] for p in portfolio_performance) if portfolio_performance else 0:.2f}%")

# Best & Worst weeks
if weekly_results:
    best_week = max(weekly_results, key=lambda x: x['total_pnl'])
    worst_week = min(weekly_results, key=lambda x: x['total_pnl'])

    print(f"\nBest Week: Week {best_week['week']} ({best_week['week_start']}) - P&L: ${best_week['total_pnl']:,.2f} ({best_week['avg_return_pct']:.2f}%)")
    print(f"Worst Week: Week {worst_week['week']} ({worst_week['week_start']}) - P&L: ${worst_week['total_pnl']:,.2f} ({worst_week['avg_return_pct']:.2f}%)")

# Save results
output_data = {
    'period': {'start': start_date.strftime('%Y-%m-%d'), 'end': end_date.strftime('%Y-%m-%d')},
    'universe_size': len(STOCK_UNIVERSE),
    'total_weeks': len(weekly_results),
    'summary': {
        'total_trades': total_trades,
        'winning_trades': total_wins,
        'losing_trades': total_losses,
        'win_rate_pct': round((total_wins/total_trades*100) if total_trades > 0 else 0, 2),
        'total_pnl': round(total_pnl, 2),
        'avg_pnl_per_trade': round(total_pnl/total_trades if total_trades > 0 else 0, 2),
        'avg_weekly_return_pct': round(avg_return, 2),
        'cumulative_return_pct': round(sum(p['return_pct'] for p in portfolio_performance), 2)
    },
    'weekly_results': weekly_results,
    'all_trades': all_trades
}

with open('outputs/weekly_top5_backtest.json', 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"\n✓ Detailed results saved to: outputs/weekly_top5_backtest.json\n")
print("=" * 100)
