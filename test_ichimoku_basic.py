#!/usr/bin/env python
"""Basic test for Ichimoku indicator integration."""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from src.indicators.ichimoku import IchimokuIndicators
from src.analysis.technical_score import TechnicalScoreCalculator

# Test 1: Ichimoku indicator calculation
print("=" * 60)
print("TEST 1: Ichimoku Indicator Calculation")
print("=" * 60)

end = datetime.now()
start = end - timedelta(days=365)
df = yf.download('AAPL', start=start, end=end, progress=False)

# Normalize columns (yfinance may return MultiIndex)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

df_ichimoku = IchimokuIndicators.calculate_ichimoku(df)

print(f"✓ Ichimoku 계산 성공")
print(f"  행 수: {len(df_ichimoku)}")
print(f"  추가된 컬럼: {[c for c in df_ichimoku.columns if 'Ichimoku' in c]}")

if len(df_ichimoku) > 0:
    latest = df_ichimoku.iloc[-1]
    print(f"  최신 값 (마지막 날짜):")
    print(f"    Close: {latest['Close']:.2f}")
    print(f"    Tenkan: {latest.get('Ichimoku_Tenkan', 0):.2f}")
    print(f"    Kijun: {latest.get('Ichimoku_Kijun', 0):.2f}")
    print(f"    SenkouA: {latest.get('Ichimoku_SenkouA', 0):.2f}")
    print(f"    SenkouB: {latest.get('Ichimoku_SenkouB', 0):.2f}")

# Test 2: Ichimoku score calculation
print("\n" + "=" * 60)
print("TEST 2: Ichimoku Score Calculation")
print("=" * 60)

calculator = TechnicalScoreCalculator()
ichimoku_score = calculator.calculate_ichimoku_score(df_ichimoku)

print(f"✓ Ichimoku 점수 계산 성공")
print(f"  점수: {ichimoku_score:.1f}/100")

# Test 3: Overall technical score with Ichimoku
print("\n" + "=" * 60)
print("TEST 3: Overall Technical Score with Ichimoku")
print("=" * 60)

overall_score, components = calculator.calculate_overall_technical_score(df_ichimoku)

print(f"✓ 종합 기술 점수 계산 성공")
print(f"  전체 점수: {overall_score:.1f}/100")
print(f"  컴포넌트 점수:")
for key, value in components.items():
    if key != 'volume_flow_detail':
        print(f"    {key}: {value}")

# Test 4: TECHNICAL_WEIGHTS validation
print("\n" + "=" * 60)
print("TEST 4: TECHNICAL_WEIGHTS Validation")
print("=" * 60)

from config.settings import TECHNICAL_WEIGHTS

print(f"✓ TECHNICAL_WEIGHTS 로드 성공")
print(f"  가중치:")
for key, value in TECHNICAL_WEIGHTS.items():
    print(f"    {key}: {value}")

total_weight = sum(TECHNICAL_WEIGHTS.values())
print(f"  합계: {total_weight:.1f}")

if abs(total_weight - 100) < 0.01:
    print(f"  ✓ 가중치 합계가 100입니다")
else:
    print(f"  ✗ 경고: 가중치 합계가 {total_weight:.1f}입니다")

print("\n" + "=" * 60)
print("모든 테스트 완료!")
print("=" * 60)
