# 🚀 Quick Start Guide

완전히 구현된 US Stock AI Analyzer를 5분 안에 시작하세요.

---

## 📋 필수사항

- Python 3.10 이상
- API Keys:
  - [NewsAPI](https://newsapi.org/) 계정
  - [Anthropic Claude](https://console.anthropic.com/) API 키

---

## ⚡ 5분 설정

### 1️⃣ 환경 준비

```bash
cd d:\claude_code\us_stock_analyzer

# 가상 환경 생성
python -m venv venv
venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2️⃣ API 키 설정

```bash
# .env 파일 생성
copy .env.example .env
```

`.env` 파일에 다음 정보를 추가:

```env
NEWS_API_KEY=your_newsapi_key_here
ANTHROPIC_API_KEY=your_claude_api_key_here
```

---

## 🏃 3가지 사용 방법

### 방법 1️⃣: 현재 주식 분석 (실시간 추천)

```bash
# 전체 S&P 100 + NASDAQ 100 분석 (130+ 종목)
python main.py

# 특정 종목만 분석
python main.py --tickers AAPL MSFT GOOGL AMZN NVDA

# 캐시된 데이터로 리포트만 재생성
python main.py --report-only
```

**예상 시간**: 5-10분 (API 호출 시간에 따라)

**결과**: `outputs/` 폴더에 생성됨
- `top5_recommendations_YYYY-MM-DD.md` - 추천 리포트
- `analysis_data_YYYY-MM-DD.json` - 상세 데이터

### 방법 2️⃣: 성능 검증 (백테스트)

```bash
# 과거 5년 데이터로 전략 검증
python backtest.py

# 커스텀 기간 백테스트
python backtest.py --years 3 --lookback 180
```

**예상 시간**: 30-60분 (티커 수에 따라)

**결과**: 
- `outputs/backtest_results_YYYY-MM-DD_HHMMSS.json` - 상세 결과
- `outputs/backtest_report_YYYY-MM-DD_HHMMSS.md` - 성능 리포트

**로그 출력 예**:
```
======================================================================
📊 BACKTEST RESULTS SUMMARY
======================================================================
Tests Completed: 45/52
Win Rate (5% Target): 58.3%
Average Gain (1 Week): 4.8%
Best Performance: 12.5%
Worst Performance: -8.2%
======================================================================
✅ RESULT: Strategy shows STRONG predictive power (>60% win rate)
```

### 방법 3️⃣: 통합 테스트 (검증)

```bash
# 모든 컴포넌트 동작 확인
python test_integration.py
```

**예상 시간**: 1-2분

**검증 항목**:
1. ✅ Ticker Manager (S&P 100 + NASDAQ 100)
2. ✅ Stock Data Collection (yfinance)
3. ✅ Technical Indicators (SMA, EMA, RSI, MACD, BB, ATR, etc.)
4. ✅ Technical Score Calculation
5. ✅ Supply/Demand Analysis (VWAP, Volume, Fibonacci)
6. ✅ Sentiment Analysis
7. ✅ Ranking System
8. ✅ Report Generation

---

## 📊 분석 구조 (Technical Architecture)

### 데이터 수집 (Data Collection)
```
Stock Data (yfinance)  ──┐
                         ├──> 기술적 지표 계산
News Data (NewsAPI)    ──┘
```

### 점수 계산 (Scoring)
```
기술적 지표 60%:
├─ Moving Averages (25%) ─── SMA 20/50/200, EMA 12/26, VWAP
├─ Momentum (20%) ─── RSI, MACD, Stochastic
├─ Volatility (15%) ─── Bollinger Bands, ATR, Keltner
├─ Volume Flow (15%) ─── OBV, MFI, A/D Line
├─ Fibonacci (10%) ─── Retracement Levels
└─ Supply/Demand (15%) ─── VWAP Position, Volume Spike, Institutional Flow, ATR Filter

감성 분석 40%:
├─ VADER (속도 최적화)
└─ Claude AI (고급 분석)

최종 점수 = 기술(60%) + 감성(40%)
```

### 추천 생성 (Top 5 Extraction)
```
All Stocks Ranked ──> Filter (ATR >= 2.5%) ──> Top 5
```

---

## 📈 예상 성능

백테스트 결과 (과거 5년):

| 메트릭 | 예상값 | 해석 |
|--------|--------|------|
| Win Rate | 50-65% | 5% 이상 상승 종목 비율 |
| Avg Gain | 4-6% | 1주일 평균 수익률 |
| Best Week | 10-15% | 최고 성과 주 |
| Worst Week | -5 ~ 0% | 최악 성과 주 |

**주의**: 이는 과거 성과이며 미래를 보장하지 않습니다.

---

## 🔧 커스터마이징

### 가중치 조정

`config/settings.py` 수정:

```python
TECHNICAL_WEIGHTS = {
    "moving_averages": 30,      # 30% (기본)
    "momentum": 20,             # 20%
    "volatility": 20,           # 20%
    "volume_flow": 20,          # 20%
    "fibonacci": 10,            # 10%
}

ENSEMBLE_WEIGHTS = {
    "technical": 0.60,          # 60%
    "sentiment": 0.40,          # 40%
}
```

### 분석 기간 변경

```bash
# 6개월 데이터로 분석
python main.py --period-days 180

# 1년 데이터로 백테스트
python backtest.py --lookback 365
```

### 특정 종목군만 분석

`data/tickers/sp100_nasdaq100.json` 수정 또는:

```bash
python main.py --tickers AAPL MSFT GOOGL AMZN NVDA NVDA TSLA
```

---

## 📁 출력 파일 구조

```
outputs/
├── top5_recommendations_2026-07-24.md          # 최종 추천
├── analysis_data_2026-07-24.json               # 상세 분석 데이터
├── backtest_results_2026-07-24_143022.json     # 백테스트 결과
└── backtest_report_2026-07-24_143022.md        # 백테스트 리포트

data/cache/
├── stock_data/                                 # 캐시된 주가 데이터
└── news_data/                                  # 캐시된 뉴스

logs/
└── analysis.log                                # 상세 로그
```

---

## 🐛 트러블슈팅

### Q1: "NEWS_API_KEY not configured" 에러

```
→ .env 파일에 NEWS_API_KEY 설정 확인
→ API 키 유효성 확인: https://newsapi.org
```

### Q2: "Failed to fetch data for ticker" 경고

```
→ 이는 정상 (일부 구 종목이나 거래 중단된 종목)
→ 다른 종목은 정상 분석됨
```

### Q3: 데이터가 너무 오래됨

```bash
# 캐시 초기화
python main.py --clear-cache

# 재실행
python main.py
```

### Q4: 백테스트가 느림

```bash
# 기간 단축
python backtest.py --years 2 --lookback 180
```

---

## 🚀 다음 단계

### Phase 1: 현재 (완료)
- ✅ 기술적 지표 분석
- ✅ 감성 분석
- ✅ Top 5 추천
- ✅ 백테스트 검증

### Phase 2: 추천 (향후)
1. **실시간 대시보드** (React + D3)
   ```bash
   npm install
   npm run dev
   ```

2. **자동 스케줄 실행** (GitHub Actions)
   ```yaml
   # .github/workflows/weekly_analysis.yml
   schedule:
     - cron: '0 17 * * 5'  # 매주 금요일 5시
   ```

3. **고급 기술적 지표**
   - Elliott Wave
   - Ichimoku Cloud
   - 머신러닝 기반 예측

4. **성과 추적**
   - 실제 거래 vs 추천 비교
   - 월간 성과 리포트
   - 동적 가중치 최적화

---

## 📞 지원 & 피드백

- **Issues**: 버그 리포트는 GitHub Issues에서
- **Discussions**: 기능 요청 및 토론
- **Documentation**: [README.md](README.md) 참고

---

## ⚠️ 면책 조항

이 프로젝트는 **교육 목적**으로만 제공되며:

- ❌ 투자 자문이 아닙니다
- ❌ 과거 성과가 미래를 보장하지 않습니다
- ❌ 실제 투자 전에 전문가 상담이 필수입니다
- ⚠️ 자신의 책임 하에 사용하세요

---

**Happy analyzing! 📊**

*마지막 업데이트: 2026-07-24*
