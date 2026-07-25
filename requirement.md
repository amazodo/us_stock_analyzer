# Requirements Specification: US Top Stock AI Recommender

## 1. Project Overview
미국 시가총액 상위 종목(S&P 100 및 NASDAQ 100)을 대상으로 기술적 지표 분석, 수급 분석, 거시경제/종목 뉴스 감성 분석을 결합하여 **1주일 이내 5% 이상 상승 가능성이 가장 높은 Top 5 종목**을 식별하고 명확한 투자 근거 리포트를 생성하는 시스템.

---

## 2. Key Target Universe
- **S&P 100** 기준 시가총액 상위 100개 종목
- **NASDAQ 100** 기준 시가총액 상위 100개 종목
- 중복 제거 후 통합 유니버스 구성 (약 130~150개 내외)

---

## 3. Functional Requirements

### 3.1 Data Collection Module
1. **주가 및 거래량 데이터 (Stock Data)**
   - 최근 1~2년일봉/시간봉 OHLCV(Open, High, Low, Close, Volume) 수집 (`yfinance` 활용).
2. **뉴스 및 거시경제 데이터 (News Data)**
   - 미 연준(Fed), 금리, CPI, 빅테크 관련 **거시경제(Macro) 뉴스** 수집.
   - 각 대상 종목별 **최신 7일간 실적/호재/악재 뉴스** 리서치.

### 3.2 Technical & Volume Indicators Calculation
다음 10가지 지표를 정확히 산출:
1. **SMA (Simple Moving Average)**: 5, 20, 50, 200일 이동평균선
2. **EMA (Exponential Moving Average)**: 9, 12, 26일 지수 이동평균선
3. **RSI (Relative Strength Index)**: 14일 기준 (과매수 70 / 과매도 30 체크)
4. **MACD**: MACD Line, Signal Line, Histogram (12, 26, 9)
5. **Bollinger Bands**: 20일 기준 (2 표준편차 상/하단 및 Bandwidth)
6. **OBV (On-Balance Volume)**: 누적 거래량 수급 흐름
7. **ATR (Average True Range)**: 14일 변동성 폭 측정 (5% 목표 타당성 검증용)
8. **Stochastic Oscillator**: %K, %D (14, 3, 3)
9. **VWAP (Volume Weighted Average Price)**: 매수 주체 평단가 추정
10. **Fibonacci Retracement**: Recent High/Low 기준 0.236, 0.382, 0.5, 0.618 지지/저항 라인 계산

### 3.3 Scoring & AI Screening Model
1. **Technical Score (0~100점)**:
   - 정배열 여부, 골든크로스, 볼린저밴드 하단 반등, OBV 상승세, 스토캐스틱 과매도 탈출 등 가중치 적용.
   - ATR 값 기반으로 **"1주일 내 5% 상승이 물리적으로 가능한 변동성을 가졌는가"** 필터링.
2. **News Sentiment Score (-50 ~ +50점)**:
   - 거시경제 뉴스 영향도 산출.
   - 종목별 최신 뉴스 텍스트 감성 분석 (긍정/부정/중립 및 호재 파급력 평가).
3. **Combined Scoring & Ranking**:
   - `Final Score = (Technical Score * 0.6) + (Sentiment Score * 0.4) + (Volume Trend Bonus)`
   - 상위 Top 5 종목 최종 선정.

### 3.4 Report Generation Module
최종 5개 종목 각각에 대해 아래 형식의 Markdown 리포트 자동 작성:
- **종목명 및 티커** (예: NVDA, AAPL)
- **추천 핵심 요약** (3줄 요약)
- **1주일 내 5% 상승 근거**:
  1. 기술적 분석 (RSI, MACD, 이동평균선, 피보나치 지지점)
  2. 수급 및 변동성 (OBV, VWAP, ATR 기반 목표가 산정)
  3. 최근 거시경제 & 종목 뉴스 호재 요약
- **손절가(Stop Loss) 및 1차 목표가(Target Price)** 설정

### 3.5 이벤트 & 옵션/시장 환경 필터링 (Market & Event Filter)
- **Earnings Calendar Check**: 향후 7일 이내 실적 발표 예정 종목 사전 경고/필터링
- **Market Regime Check**: SPY/QQQ의 20일 이평선 유무 및 VIX 지수로 시장 리스크 등급(Safe / Caution / Risk-Off) 산출
- **Sector Momentum**: 11개 주요 섹터 ETF 상승률을 바탕으로 주도 섹터 가산점 부여

### 3.6 손익비 및 스윙 타겟 계산 (Risk/Reward Calculator)
- **ATR 및 피보나치 기반 손절가/목표가 계산**:
  - Target Price: +5.0% 이상 (피보나치 저항 라인 고려)
  - Stop Loss: -2.0% ~ -3.0% (피보나치 지지 라인 또는 ATR 1.5배 하단)
- **Risk/Reward Ratio**: 손익비가 1:2 이상(예: 위험 2.5% 대비 기대수익 5.0% 이상)인 종목만 랭킹 상위 등록
---

## 4. Non-Functional Requirements
- **실행 속도**: API 요청 쿼리 캐싱(Cache) 처리로 재실행 시 데이터 재요청 최소화.
- **오류 처리**: 상장 폐지, 데이터 누락 티커에 대한 Exception Handling 구현.
- **설정 변경 용이성**: 가중치 및 필터 조건은 `config/settings.py`에서 손쉽게 수정할 수 있도록 분리.