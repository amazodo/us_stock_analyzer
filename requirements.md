# 📊 US Stock AI Analyzer - 요구사항 정의서

## 프로젝트 개요
본 프로젝트는 미국 시가총액 상위 종목(S&P 100 및 NASDAQ 100 통합 유니버스, 약 130~150개)을 대상으로 기술적 지표, 수급 분석, 뉴스 감성 분석, 시장/이벤트 리스크를 종합하여 1주일 이내 5% 이상 상승 가능성이 가장 높은 Top 5 종목을 식별하고, Streamlit 기반 대시보드 웹앱을 통해 시각화 차트와 다각도 분석 근거를 제공하는 AI 시스템이다.

---

## 핵심 기능 요구사항

### 1. 데이터 수집 (Data Collection)
- **대상 유니버스**: S&P 100 및 NASDAQ 100 시가총액 상위 종목 (중복 제거 후 약 130~150개 티커 리스트 관리)
- **주가 데이터**: yfinance를 통한 일중/주간/월간 가격, 거래량, 수익률
- **뉴스 데이터**: NewsAPI, Google News를 통한 거시경제 & 종목별 뉴스 수집
- **캐싱 전략**: API 호출 최소화를 위한 로컬 캐시 (매일/주간 갱신)
- **거래 시간대**: 미국 장 시간대(09:30~16:00 EST)에 맞춘 데이터 수집

### 2. 기술적 지표 분석 (Technical Indicators)

#### 이동평균 (Moving Averages)
- SMA (Simple Moving Average): 20일, 50일, 200일
- EMA (Exponential Moving Average): 12일, 26일
- VWAP (Volume Weighted Average Price)

#### 모멘텀 지표 (Momentum)
- RSI (14일): 과매수/과매도 판단
- MACD: 추세 전환 신호
- Stochastic: %K, %D 라인

#### 변동성 지표 (Volatility)
- Bollinger Bands: 상단/중앙/하단
- ATR (Average True Range): 변동성 크기
- Beta: 시장 대비 민감도

#### 거래량 & 수급 (Volume & Flow)
- OBV (On-Balance Volume): 누적 거래량 추세
- **수급 강도 추정**: VWAP 대비 현재가 위치, 거래량 급증(Volume Spike), Volume Profile(주요 매물대)을 통한 세력/기관 수급 유입 추정
- **ATR 변동성 필터**: (14일 ATR / 현재가) 비율을 계산하여 1주일 내 5% 목표 달성이 물리적으로 가능한 변동성을 가졌는지 사전 검증

### 3. 피보나치 분석 (Fibonacci Retracement)
- 최근 상승/하락 구간에서 38.2%, 50%, 61.8% 지지/저항 수준 계산
- 스윙 고점/저점 기반 계산

### 4. 감성 분석 (Sentiment Analysis)

#### 방법 1: VADER (Valence Aware Dictionary)
- 속도 우선, 오프라인 처리

#### 방법 2: LLM 기반 (Claude API)
- 더 정교한 감성 평가
- 맥락 이해 및 시장 영향 분석

### 5. 최종 랭킹 및 추천
- **정량 점수** (기술적 지표):
  - 이동평균 추세 (30점)
  - RSI/MACD (20점)
  - 변동성 (20점)
  - 거래량/수급 (20점)
  - 피보나치 지지/저항 (10점)
  - **합계: 100점**

- **정성 점수** (뉴스 감성):
  - 거시경제 뉴스 감성 (30점)
  - 개별 종목 뉴스 감성 (40점)
  - 전문가 평가 (30점)
  - **합계: 100점**

- **최종 점수**: 정량 60% + 정성 40% = 최종 랭킹
- **Top 5 종목 추출** 및 각 종목별 분석 리포트 생성

### 6. 리포트 생성 (Report Generation)
1. Streamlit 대시보드 UI/UX 요구사항
2.1 사이드바 사용자 입력 파라미터 (User Inputs)
Streamlit 사이드바(Sidebar) 영역에 아래 컨트롤을 제공한다.

분석 데이터 수집 기간 (History Period):

설정 방식: 슬라이더 또는 숫자 입력 필드 (단위: 월 / Month)

기본값: 12개월 (1년)

설정 범위: 최소 1개월 ~ 최대 240개월 (20년)

Top 5 분석 적용 기법 선택 (Indicator & Analysis Multi-select):

사용자가 분석 및 점수 산정에 반영할 지표/기법을 체크박스/멀티선택으로 지정 가능:

[x] 이동평균선 (SMA / EMA)

[x] 모멘텀 지표 (RSI / MACD / Stochastic)

[x] 변동성 지표 (Bollinger Bands / ATR)

[x] 거래량 & 수급 지표 (OBV / VWAP / Volume Profile)

[x] 피보나치 되돌림 (Fibonacci Retracement)

[x] 뉴스 감성 분석 (LLM / VADER)

[x] 섹터 모멘텀 & 시장 환경 (Sector Relative Strength)

분석 실행 버튼 (Run Analysis Button):

설정한 조건 및 기간으로 분석 파이프라인을 실행하는 대형 Action Button.

2.2 메인 화면 메인 뷰 (Main Dashboard Output)
뷰 A: Top 5 추천 요약 대시보드
Top 5 종목 메트릭 카드가 한눈에 표시 (티커, 현재가, 1주일 목표가 [+5% 이상], 손절가, 예상 손익비, 종합 점수).

시장 환경 상태 (Market Regime Badge): SPY/QQQ 20일선 및 VIX 기반 시장 리스크 등급 표시 (Safe / Caution / Risk-Off).

뷰 B: Top 5 개별 종목 상세 분석 (탭 또는 드롭다운 선택)
선택한 종목에 대해 3가지 영역으로 구분하여 제공:

인터랙티브 주식 차트 (Yahoo Finance 스타일):

plotly / lightweight-charts 활용.

시간축 변환: 일봉(1D), 주봉(1W), 월봉(1M) 및 기간 선택 (1개월~전체).

지표 On/Off 토글: 선택한 이동평균선(20/50/200), 볼린저밴드, VWAP, 피보나치 지지/저항 라인 차트 오버레이.

하단 보조 지표 차트: 거래량(Volume), MACD, RSI, OBV 보조 차트 전환 기능.

분석 기법별 추천 근거 정리 (Detailed Technical & Fundamental Rationale):

기술적/수급 점수 세부 내역: 선택된 각 기법(이동평균, RSI/MACD, OBV/VWAP, 피보나치)별 상태 및 점수 기여도 표기.

1주일 5% 상승 시나리오:

ATR 기준 5% 변동 가능성 수용 여부.

주요 지지 라인(손절가) 및 저항 라인(목표가) 기반 손익비(Risk/Reward Ratio, 최소 1:2 권장) 도출.

향후 7일 이내 실적 발표/이벤트 일정 체크 결과 (실적 리스크 경고).

최신 재료 뉴스 & 감성 분석 (Latest News & Catalyst):

최근 7일간 관련 핵심 뉴스의 헤드라인, 요약, 출처 링크 제공.

LLM/VADER 감성 분석 점수 (Positive / Neutral / Negative) 및 주가 호재 요인 3줄 요약.

2. PDF 변환 옵션


---

## 기술 스택
Frontend / UI: streamlit, plotly (또는 st-lightweight-charts)

Backend / Analysis: Python 3.10+, pandas, numpy, ta (또는 pandas_ta)

Data Source: yfinance, NewsAPI / Tavily API

AI / LLM: Anthropic Claude API (뉴스 요약 및 종합 근거 생성)

Caching & Storage: @st.cache_data, PyArrow / Parquet

### 백엔드
핵심 백엔드 기능 요구사항
#### 데이터 수집 (Data Collection)
유니버스: S&P 100 및 NASDAQ 100 통합 유니버스 (중복 제거 후 약 130~150개 티커).

주가 데이터: yfinance를 활용하여 사용자가 설정한 기간(1~240개월)의 OHLCV 데이터 수집.

뉴스 데이터: NewsAPI / Google News / Tavily를 통한 거시경제 및 개별 종목 최신 뉴스 수집.

이벤트 & 캘린더: 향후 7일 내 실적 발표(Earnings Call) 일정 수집.

캐싱 전략: Streamlit @st.cache_data 및 로컬 캐시(JSON/Parquet)를 활용하여 API 호출 및 분석 속도 최적화.

#### 분석 엔진 (Analysis Engine)
1) 기술적 및 수급 지표 계산 (10대 지표)
이동평균: SMA (20, 50, 200일), EMA (12, 26일)

모멘텀: RSI (14일), MACD (12, 26, 9), Stochastic (%K, %D)

변동성: Bollinger Bands (20일, 2σ), ATR (14일 - 5% 변동성 검증용)

수급 & 거래량: OBV (누적 수급), VWAP (매수 주체 평단가), Volume Profile

피보나치: 스윙 고점/저점 기반 0.382, 0.5, 0.618 되돌림 지지/저항 라인 산출

2) 필터링 & 가중치 Scoring
ATR 변동성 필터: (14일 ATR / 현재가) >= 2.5% 기준을 통해 1주일 내 5% 움직일 에너지가 부족한 대형 고정주 제외.

실적 리스크 필터: 7일 이내 실적 발표 예정주는 주의/감점 처리.

점수산정: 사용자가 선택한 기법들의 점수를 정규화 합산:

최종 점수 = (선택된 기술/수급 지표 점수 * 0.6) + (뉴스 감성 점수 * 0.4) + (섹터 모멘텀 가산점)


### 데이터 저장
- **로컬 캐시**: JSON/CSV (data/cache/)
- **Optional**: SQLite 또는 PostgreSQL

### 배포
- **GitHub**: 코드 저장소
- **Netlify/Vercel**: 정적 리포트 호스팅 (Optional)
- **GitHub Actions**: 자동 분석 스케줄 실행

---

## 설정 및 환경 변수

### `.env` 파일 구성
```
# API Keys
NEWS_API_KEY=your_newsapi_key
TAVILY_API_KEY=your_tavily_key
ANTHROPIC_API_KEY=your_claude_api_key

# 분석 설정
ANALYSIS_PERIOD_DAYS=30
TOP_N_RECOMMENDATIONS=5
TARGET_GAIN_PERCENT=5.0

# 캐시 설정
CACHE_EXPIRY_HOURS=24
ENABLE_LOCAL_CACHE=true

# 로깅
LOG_LEVEL=INFO
```

---

## 프로젝트 구조

```
us-stock-ai-analyzer/
├── CLAUDE.md                 # 프로젝트 지침
├── requirements.md           # 이 파일
├── requirements.txt          # 의존성
├── README.md                 # 사용법
├── .env.example              # 환경변수 템플릿
├── main.py                   # 메인 실행 엔트리포인트
│
├── config/
│   ├── __init__.py
│   └── settings.py           # 전역 설정 (가중치, 분석 기간 등)
│
├── data/
│   ├── tickers/              # 종목 리스트 (S&P 100, NASDAQ 100)
│   └── cache/                # 수집한 데이터 캐시
│
├── src/
│   ├── collectors/           # 데이터 수집 모듈
│   │   ├── stock_data.py     # yfinance 기반 주가 수집
│   │   └── news_data.py      # 뉴스 데이터 수집
│   │
│   ├── indicators/           # 기술적 지표 계산
│   │   ├── moving_averages.py
│   │   ├── momentum.py
│   │   ├── volatility.py
│   │   └── volume_flow.py
│   │
│   ├── analysis/             # 분석 엔진
│   │   ├── technical_score.py
│   │   ├── sentiment_score.py
│   │   └── fibonacci.py
│   ├── ui/                   # Streamlit UI 컴포넌트 (차트, 카드리포트, 뉴스 탭)
│   │   ├── sidebar.py        # 사용자 입력 파라미터
│   │   ├── charts.py         # Yahoo 스타일 Plotly 차트 컴포넌트
│   │   └── views.py          # Top 5 요약 및 상세 분석 뷰
│   └── recommender/          # 최종 추천 생성
│       ├── ranker.py
│       └── report_generator.py
│
├── tests/                    # 단위 테스트
└── outputs/                  # 생성된 리포트 (Markdown, PDF)
```

---

## 실행 흐름 (Workflow)

```
1. main.py 실행
2. 설정 로드 (config/settings.py)
3. 티커 리스트 로드 (data/tickers/)
4. 데이터 수집
   - 주가 데이터 (collectors/stock_data.py)
   - 뉴스 데이터 (collectors/news_data.py)
5. 기술적 지표 계산 (src/indicators/)
6. 피보나치 분석 (analysis/fibonacci.py)
7. 감성 분석 (analysis/sentiment_score.py)
8. 점수 계산
   - 기술적 점수 (analysis/technical_score.py)
   - 감성 점수 (analysis/sentiment_score.py)
9. 랭킹 생성 (recommender/ranker.py)
10. Top 5 추출
11. 리포트 생성 (recommender/report_generator.py)
12. outputs/ 에 저장
```

---

## 성공 기준

✅ **필수 (MVP)**
- [ ] **S&P 100 & NASDAQ 100 통합 유니버스(130+ 종목)** 전체 기술적/수급 지표 계산
- [ ] 거시경제 및 개별 종목 뉴스 감성 분석 (VADER + LLM)
- [ ] **1주일 내 5% 상승 가능성 Top 5 추천** + 상세 근거 리포트 생성 (Markdown/PDF)
- [ ] 자동 스케줄 실행 (주 1회)
- [ ] 백테스트 & 성과 추적
- [ ] 고급 기술적 지표 (Elliott Wave, Ichimoku)
✅ **선택사항 (Phase 2)**
- [ ] 실시간 대시보드 (React + D3)
- [ ] 백테스트 & 성과 추적
- [ ] 고급 기술적 지표 (Elliott Wave, Ichimoku)
- [ ] 머신러닝 기반 예측

---

## 참고사항

- **데이터 신뢰성**: yfinance는 지연된 데이터 (15-20분 딜레이)
- **API 호출 제한**: NewsAPI는 월 500회 무료 제한
- **시간대**: 미국 동부 시간(EST) 기준 분석
- **리스크**: 과거 성과는 미래를 보장하지 않음 (면책 조항 포함)
