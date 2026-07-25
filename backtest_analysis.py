#!/usr/bin/env python
"""
Backtest Results Analysis & Visualization
- Weekly performance trends
- Win rate analysis
- Score correlation
- Market regime detection
"""

import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Load backtest results
with open('outputs/weekly_top5_backtest_improved.json', 'r') as f:
    data = json.load(f)

weekly_results = data['weekly_results']
print("=" * 120)
print("WEEKLY BACKTEST ANALYSIS & PERFORMANCE BREAKDOWN")
print("=" * 120)

# Convert to DataFrame for easier analysis
df_weekly = pd.DataFrame([
    {
        'week': w['week'],
        'week_start': w['week_start'],
        'top5': ', '.join(w['top5']),
        'avg_score': np.mean(w['top5_scores']),
        'trades': w['total_trades'],
        'wins': w['winning_trades'],
        'losses': w['losing_trades'],
        'win_rate': w['win_rate_pct'],
        'total_pnl': w['total_pnl'],
        'avg_return': w['avg_return_pct'],
        'cum_return': w['total_return_pct']
    }
    for w in weekly_results
])

print("\n" + "DETAILED WEEKLY BREAKDOWN".center(120))
print("=" * 120)
print(f"{'Week':<6} {'Start Date':<12} {'Avg Score':<11} {'Trades':<8} {'Wins':<6} {'Win%':<8} {'Avg%':<10} {'Total P&L':<12}")
print("-" * 120)

for idx, row in df_weekly.iterrows():
    print(f"{row['week']:<6} {row['week_start']:<12} {row['avg_score']:>9.1f} {row['trades']:<8} "
          f"{row['wins']:<6} {row['win_rate']:>6.1f}% {row['avg_return']:>9.2f}% ${row['total_pnl']:>10.2f}")

# Analyze performance phases
print("\n" + "=" * 120)
print("PERFORMANCE ANALYSIS BY PHASE")
print("=" * 120)

# Phase 1: Summer (Weeks 1-13, Jul-Sep)
phase1 = df_weekly[df_weekly['week'] <= 13]
print(f"\nPHASE 1 - Summer (Jul-Sep, Weeks 1-13):")
print(f"  Average Return: {phase1['avg_return'].mean():.2f}%")
print(f"  Win Rate: {phase1['win_rate'].mean():.1f}%")
print(f"  Total P&L: ${phase1['total_pnl'].sum():.2f}")
print(f"  Avg Score: {phase1['avg_score'].mean():.1f}")
print(f"  Best Week: Week {phase1.loc[phase1['total_pnl'].idxmax(), 'week']:.0f} (${phase1['total_pnl'].max():.2f})")
print(f"  Worst Week: Week {phase1.loc[phase1['total_pnl'].idxmin(), 'week']:.0f} (${phase1['total_pnl'].min():.2f})")

# Phase 2: Fall (Weeks 14-26, Oct-Dec)
phase2 = df_weekly[(df_weekly['week'] > 13) & (df_weekly['week'] <= 26)]
print(f"\nPHASE 2 - Fall (Oct-Dec, Weeks 14-26):")
print(f"  Average Return: {phase2['avg_return'].mean():.2f}%")
print(f"  Win Rate: {phase2['win_rate'].mean():.1f}%")
print(f"  Total P&L: ${phase2['total_pnl'].sum():.2f}")
print(f"  Avg Score: {phase2['avg_score'].mean():.1f}")
print(f"  Best Week: Week {phase2.loc[phase2['total_pnl'].idxmax(), 'week']:.0f} (${phase2['total_pnl'].max():.2f})")
print(f"  Worst Week: Week {phase2.loc[phase2['total_pnl'].idxmin(), 'week']:.0f} (${phase2['total_pnl'].min():.2f})")

# Phase 3: Winter (Weeks 27-39, Jan-Mar)
phase3 = df_weekly[(df_weekly['week'] > 26) & (df_weekly['week'] <= 39)]
print(f"\nPHASE 3 - Winter (Jan-Mar, Weeks 27-39):")
print(f"  Average Return: {phase3['avg_return'].mean():.2f}%")
print(f"  Win Rate: {phase3['win_rate'].mean():.1f}%")
print(f"  Total P&L: ${phase3['total_pnl'].sum():.2f}")
print(f"  Avg Score: {phase3['avg_score'].mean():.1f}")
print(f"  Best Week: Week {phase3.loc[phase3['total_pnl'].idxmax(), 'week']:.0f} (${phase3['total_pnl'].max():.2f})")
print(f"  Worst Week: Week {phase3.loc[phase3['total_pnl'].idxmin(), 'week']:.0f} (${phase3['total_pnl'].min():.2f})")

# Phase 4: Spring (Weeks 40-51, Apr-Jul)
phase4 = df_weekly[df_weekly['week'] > 39]
print(f"\nPHASE 4 - Spring (Apr-Jul, Weeks 40-51):")
print(f"  Average Return: {phase4['avg_return'].mean():.2f}%")
print(f"  Win Rate: {phase4['win_rate'].mean():.1f}%")
print(f"  Total P&L: ${phase4['total_pnl'].sum():.2f}")
print(f"  Avg Score: {phase4['avg_score'].mean():.1f}")
print(f"  Best Week: Week {phase4.loc[phase4['total_pnl'].idxmax(), 'week']:.0f} (${phase4['total_pnl'].max():.2f})")
print(f"  Worst Week: Week {phase4.loc[phase4['total_pnl'].idxmin(), 'week']:.0f} (${phase4['total_pnl'].min():.2f})")

# Top & Bottom performers
print("\n" + "=" * 120)
print("TOP 10 BEST & WORST PERFORMING WEEKS")
print("=" * 120)

print("\n✓ TOP 10 BEST WEEKS:")
print("-" * 120)
top_weeks = df_weekly.nlargest(10, 'total_pnl')[['week', 'week_start', 'top5', 'avg_score', 'win_rate', 'total_pnl', 'avg_return']]
for idx, row in top_weeks.iterrows():
    print(f"  Week {row['week']:<2} ({row['week_start']}): {row['top5'][:40]:<40}")
    print(f"    → Score: {row['avg_score']:.1f}, Win%: {row['win_rate']:.0f}%, P&L: ${row['total_pnl']:.2f}, Return: {row['avg_return']:.2f}%\n")

print("\n✗ TOP 10 WORST WEEKS:")
print("-" * 120)
worst_weeks = df_weekly.nsmallest(10, 'total_pnl')[['week', 'week_start', 'top5', 'avg_score', 'win_rate', 'total_pnl', 'avg_return']]
for idx, row in worst_weeks.iterrows():
    print(f"  Week {row['week']:<2} ({row['week_start']}): {row['top5'][:40]:<40}")
    print(f"    → Score: {row['avg_score']:.1f}, Win%: {row['win_rate']:.0f}%, P&L: ${row['total_pnl']:.2f}, Return: {row['avg_return']:.2f}%\n")

# Win rate distribution
print("\n" + "=" * 120)
print("WIN RATE DISTRIBUTION")
print("=" * 120)
win_rate_100 = len(df_weekly[df_weekly['win_rate'] == 100.0])
win_rate_80 = len(df_weekly[df_weekly['win_rate'] == 80.0])
win_rate_60 = len(df_weekly[df_weekly['win_rate'] == 60.0])
win_rate_40 = len(df_weekly[df_weekly['win_rate'] == 40.0])
win_rate_20 = len(df_weekly[df_weekly['win_rate'] == 20.0])
win_rate_0 = len(df_weekly[df_weekly['win_rate'] == 0.0])

print(f"\n  100% Win Rate (5/5):  {win_rate_100:2d} weeks {('█' * win_rate_100).ljust(20)}")
print(f"   80% Win Rate (4/5):  {win_rate_80:2d} weeks {('█' * win_rate_80).ljust(20)}")
print(f"   60% Win Rate (3/5):  {win_rate_60:2d} weeks {('█' * win_rate_60).ljust(20)}")
print(f"   40% Win Rate (2/5):  {win_rate_40:2d} weeks {('█' * win_rate_40).ljust(20)}")
print(f"   20% Win Rate (1/5):  {win_rate_20:2d} weeks {('█' * win_rate_20).ljust(20)}")
print(f"    0% Win Rate (0/5):  {win_rate_0:2d} weeks {('█' * win_rate_0).ljust(20)}")

# Score vs Performance correlation
print("\n" + "=" * 120)
print("SCORE VS PERFORMANCE CORRELATION")
print("=" * 120)

correlation = df_weekly['avg_score'].corr(df_weekly['avg_return'])
print(f"\n  Correlation (Score vs Avg Return): {correlation:.3f}")
print(f"  {'Interpretation:'} {'Strong positive' if correlation > 0.6 else 'Moderate' if correlation > 0.3 else 'Weak'} correlation")

# Volatility analysis
print(f"\n  Score Volatility (Std Dev): {df_weekly['avg_score'].std():.2f}")
print(f"  Return Volatility (Std Dev): {df_weekly['avg_return'].std():.2f}%")

# Analyze worst weeks reasons
print("\n" + "=" * 120)
print("WORST WEEKS ANALYSIS - KEY FACTORS")
print("=" * 120)

worst_5_weeks = df_weekly.nsmallest(5, 'total_pnl')
for idx, row in worst_5_weeks.iterrows():
    week_data = weekly_results[int(row['week']) - 1]
    trades = week_data['trades']

    losing_trades = [t for t in trades if t['return_pct'] < 0]
    avg_loss = np.mean([t['return_pct'] for t in losing_trades]) if losing_trades else 0
    max_loss = min([t['return_pct'] for t in trades], default=0)

    print(f"\n  ⚠️  WEEK {int(row['week'])} ({row['week_start']}) - P&L: ${row['total_pnl']:.2f}, Return: {row['avg_return']:.2f}%")
    print(f"      Score: {row['avg_score']:.1f} | Top5: {row['top5']}")
    print(f"      Losing Trades: {len(losing_trades)}/5 | Avg Loss: {avg_loss:.2f}% | Worst Loss: {max_loss:.2f}%")
    print(f"      Tickers:")
    for i, trade in enumerate(trades, 1):
        symbol = '✗' if trade['return_pct'] < 0 else '✓'
        print(f"        {symbol} {trade['ticker']:6} | Score:{trade['score']:5.1f} | "
              f"Return:{trade['return_pct']:7.2f}% | P&L:${trade['profit_loss']:7.2f}")

# Analyze best weeks reasons
print("\n" + "=" * 120)
print("BEST WEEKS ANALYSIS - KEY FACTORS")
print("=" * 120)

best_5_weeks = df_weekly.nlargest(5, 'total_pnl')
for idx, row in best_5_weeks.iterrows():
    week_data = weekly_results[int(row['week']) - 1]
    trades = week_data['trades']

    winning_trades = [t for t in trades if t['return_pct'] > 0]
    avg_win = np.mean([t['return_pct'] for t in winning_trades]) if winning_trades else 0
    max_win = max([t['return_pct'] for t in trades], default=0)

    print(f"\n  ✓ WEEK {int(row['week'])} ({row['week_start']}) - P&L: ${row['total_pnl']:.2f}, Return: {row['avg_return']:.2f}%")
    print(f"      Score: {row['avg_score']:.1f} | Top5: {row['top5']}")
    print(f"      Winning Trades: {len(winning_trades)}/5 | Avg Win: {avg_win:.2f}% | Best Win: {max_win:.2f}%")
    print(f"      Tickers:")
    for i, trade in enumerate(trades, 1):
        symbol = '✓' if trade['return_pct'] > 0 else '✗'
        print(f"        {symbol} {trade['ticker']:6} | Score:{trade['score']:5.1f} | "
              f"Return:{trade['return_pct']:7.2f}% | P&L:${trade['profit_loss']:7.2f}")

print("\n" + "=" * 120)
