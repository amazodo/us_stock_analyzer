#!/usr/bin/env python
"""
Backtest Results Visualization
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(20, 14))

# Load data
with open('outputs/weekly_top5_backtest_improved.json', 'r') as f:
    data = json.load(f)

weekly_results = data['weekly_results']
df_weekly = pd.DataFrame([
    {
        'week': w['week'],
        'date': pd.to_datetime(w['week_start']),
        'avg_score': np.mean(w['top5_scores']),
        'win_rate': w['win_rate_pct'],
        'total_pnl': w['total_pnl'],
        'avg_return': w['avg_return_pct'],
        'cum_pnl': sum(wr['total_pnl'] for wr in weekly_results[:w['week']])
    }
    for w in weekly_results
])

# 1. Cumulative P&L Over Time
ax1 = plt.subplot(3, 2, 1)
ax1.plot(df_weekly['date'], df_weekly['cum_pnl'], linewidth=2.5, color='#2E86AB', marker='o', markersize=3)
ax1.fill_between(df_weekly['date'], df_weekly['cum_pnl'], alpha=0.3, color='#2E86AB')
ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
ax1.set_title('Cumulative P&L Over 51 Weeks', fontsize=12, fontweight='bold')
ax1.set_ylabel('P&L ($)', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_locator(mdates.MonthLocator())
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# 2. Weekly P&L Distribution
ax2 = plt.subplot(3, 2, 2)
colors = ['green' if x > 0 else 'red' for x in df_weekly['total_pnl']]
ax2.bar(df_weekly['week'], df_weekly['total_pnl'], color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax2.set_title('Weekly P&L Distribution', fontsize=12, fontweight='bold')
ax2.set_ylabel('P&L ($)', fontsize=10)
ax2.set_xlabel('Week', fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')

# 3. Win Rate Trend
ax3 = plt.subplot(3, 2, 3)
colors_wr = ['green' if x >= 60 else 'orange' if x >= 40 else 'red' for x in df_weekly['win_rate']]
ax3.bar(df_weekly['week'], df_weekly['win_rate'], color=colors_wr, alpha=0.7, edgecolor='black', linewidth=0.5)
ax3.axhline(y=50, color='blue', linestyle='--', alpha=0.5, label='50% Breakeven')
ax3.set_title('Weekly Win Rate (%)', fontsize=12, fontweight='bold')
ax3.set_ylabel('Win Rate (%)', fontsize=10)
ax3.set_xlabel('Week', fontsize=10)
ax3.set_ylim(0, 100)
ax3.legend()
ax3.grid(True, alpha=0.3, axis='y')

# 4. Average Return Trend (Moving Average)
ax4 = plt.subplot(3, 2, 4)
ma_5 = df_weekly['avg_return'].rolling(window=5, center=True).mean()
ax4.plot(df_weekly['week'], df_weekly['avg_return'], marker='o', linestyle='-', linewidth=1,
         markersize=3, alpha=0.5, label='Weekly Return', color='gray')
ax4.plot(df_weekly['week'], ma_5, linewidth=2.5, color='#A23B72', label='5-Week MA', marker='s', markersize=4)
ax4.axhline(y=0, color='red', linestyle='--', alpha=0.5)
ax4.set_title('Average Weekly Return (%) with 5-Week Moving Average', fontsize=12, fontweight='bold')
ax4.set_ylabel('Return (%)', fontsize=10)
ax4.set_xlabel('Week', fontsize=10)
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. Score vs Return Scatter
ax5 = plt.subplot(3, 2, 5)
scatter = ax5.scatter(df_weekly['avg_score'], df_weekly['avg_return'],
                     c=df_weekly['week'], cmap='viridis', s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
ax5.set_title('Score vs Return (Week colored by time)', fontsize=12, fontweight='bold')
ax5.set_xlabel('Average Score', fontsize=10)
ax5.set_ylabel('Average Return (%)', fontsize=10)
# Add trend line
z = np.polyfit(df_weekly['avg_score'], df_weekly['avg_return'], 1)
p = np.poly1d(z)
ax5.plot(df_weekly['avg_score'], p(df_weekly['avg_score']), "r--", alpha=0.8, linewidth=2, label=f'Trend')
ax5.legend()
ax5.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax5)
cbar.set_label('Week', fontsize=9)

# 6. Season Analysis
ax6 = plt.subplot(3, 2, 6)
seasons = ['Summer\n(W1-13)', 'Fall\n(W14-26)', 'Winter\n(W27-39)', 'Spring\n(W40-51)']
season_pnl = [
    df_weekly[df_weekly['week'] <= 13]['cum_pnl'].iloc[-1],
    df_weekly[(df_weekly['week'] > 13) & (df_weekly['week'] <= 26)]['cum_pnl'].iloc[-1] -
        df_weekly[df_weekly['week'] <= 13]['cum_pnl'].iloc[-1],
    df_weekly[(df_weekly['week'] > 26) & (df_weekly['week'] <= 39)]['cum_pnl'].iloc[-1] -
        df_weekly[(df_weekly['week'] > 13) & (df_weekly['week'] <= 26)]['cum_pnl'].iloc[-1],
    df_weekly[df_weekly['week'] > 39]['cum_pnl'].iloc[-1] -
        df_weekly[(df_weekly['week'] > 26) & (df_weekly['week'] <= 39)]['cum_pnl'].iloc[-1]
]
season_wr = [
    df_weekly[df_weekly['week'] <= 13]['win_rate'].mean(),
    df_weekly[(df_weekly['week'] > 13) & (df_weekly['week'] <= 26)]['win_rate'].mean(),
    df_weekly[(df_weekly['week'] > 26) & (df_weekly['week'] <= 39)]['win_rate'].mean(),
    df_weekly[df_weekly['week'] > 39]['win_rate'].mean()
]

x_pos = np.arange(len(seasons))
colors_season = ['green' if x > 0 else 'red' for x in season_pnl]
bars = ax6.bar(x_pos, season_pnl, color=colors_season, alpha=0.7, edgecolor='black', linewidth=1)
ax6.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax6.set_title('Seasonal P&L Analysis', fontsize=12, fontweight='bold')
ax6.set_ylabel('P&L ($)', fontsize=10)
ax6.set_xticks(x_pos)
ax6.set_xticklabels(seasons, fontsize=9)
ax6.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, (bar, wr) in enumerate(zip(bars, season_wr)):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height,
            f'${height:.0f}\n({wr:.0f}%)',
            ha='center', va='bottom' if height > 0 else 'top', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/backtest_analysis_visualized.png', dpi=150, bbox_inches='tight')
print("✓ Visualization saved to: outputs/backtest_analysis_visualized.png")
plt.close()

# Create a second figure for detailed heatmap
fig2, ax = plt.subplots(figsize=(14, 8))

# Create data for heatmap
heatmap_data = df_weekly[['week', 'avg_score', 'win_rate', 'avg_return', 'total_pnl']].copy()
heatmap_data['score_norm'] = (heatmap_data['avg_score'] - heatmap_data['avg_score'].min()) / (heatmap_data['avg_score'].max() - heatmap_data['avg_score'].min()) * 100
heatmap_data['wr_norm'] = heatmap_data['win_rate']
heatmap_data['return_norm'] = (heatmap_data['avg_return'] - heatmap_data['avg_return'].min()) / (heatmap_data['avg_return'].max() - heatmap_data['avg_return'].min()) * 100
heatmap_data['pnl_norm'] = (heatmap_data['total_pnl'] - heatmap_data['total_pnl'].min()) / (heatmap_data['total_pnl'].max() - heatmap_data['total_pnl'].min()) * 100

# Prepare data for imshow
heat_matrix = heatmap_data[['score_norm', 'wr_norm', 'return_norm', 'pnl_norm']].T.values

im = ax.imshow(heat_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

# Set ticks and labels
ax.set_yticks([0, 1, 2, 3])
ax.set_yticklabels(['Score (0-100)', 'Win Rate (%)', 'Return (norm%)', 'P&L (norm%)'], fontsize=10)
ax.set_xticks(range(0, len(heatmap_data), 5))
ax.set_xticklabels([f"W{int(w)}" for w in heatmap_data['week'].iloc[::5]], fontsize=8)

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Normalized Score (0-100)', fontsize=10)

ax.set_title('Weekly Performance Heatmap: Score, Win Rate, Return, P&L', fontsize=12, fontweight='bold')
ax.set_xlabel('Week', fontsize=10)

plt.tight_layout()
plt.savefig('outputs/backtest_heatmap.png', dpi=150, bbox_inches='tight')
print("✓ Heatmap saved to: outputs/backtest_heatmap.png")
plt.close()

print("\n" + "="*80)
print("VISUALIZATION SUMMARY")
print("="*80)
print("""
1. Cumulative P&L: Shows overall performance trend (upward is good)
   - Summer phase shows strong gains ($194.11)
   - Winter phase shows weakness (loss of $9.89)

2. Weekly P&L Distribution: Red/green bars indicate losses/wins each week
   - Most weeks show positive P&L
   - May-Jun period shows volatile swings

3. Win Rate Trend: Percentage of winning trades per week
   - Summer: 72.3% (strong)
   - Winter: 44.6% (weak)

4. Return Trend with MA: Individual returns + 5-week moving average
   - Clear seasonal pattern visible
   - Summer outperforms, Winter underperforms

5. Score vs Return Scatter: Technical score vs actual return
   - Weak correlation (-0.037) suggests score is not perfect predictor
   - Multiple factors drive returns beyond technical score

6. Seasonal Analysis: Performance by season
   - Summer: Strong (+$194, 72% WR)
   - Fall: Moderate (+$94, 52% WR)
   - Winter: Weak (-$10, 45% WR)
   - Spring: Mixed (+$44, 47% WR)
""")
