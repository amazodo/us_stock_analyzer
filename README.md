# 📊 US Stock AI Analyzer

기술적 지표 기반 **Top 5 주식 추천 시스템**
- 🚀 **Streamlit 웹앱** - 브라우저에서 실시간 분석
- 📱 **모바일 지원** - 폰에서도 접속 가능
- 📈 **6개 기술 지표** - 종합적인 기술적 분석
- 📰 **실시간 뉴스** - 각 종목별 최신 뉴스 통합

---

## 🎯 기능

### 📊 분석 기능
- **이동평균 분석** (24%)
  - SMA 20/50/200, EMA 12/26
  - 트렌드 방향 및 강도 판단

- **모멘텀 지표** (16%)
  - RSI 14 (과매수/과매도)
  - MACD (추세 확인)
  - Stochastic (반전 신호)

- **변동성 분석** (16%)
  - Bollinger Bands (가격 범위)
  - ATR (평균 진정 범위)

- **거래량/수급** (16%)
  - OBV (누적 거래량)
  - VWAP (거래량 가중 평균가)
  - Money Flow Index (자금 흐름)

- **피보나치** (8%)
  - 지지/저항선 계산
  - 반전점 확인

- **일목균형표** (20%) ⭐ NEW
  - Kumo (구름대) 분석
  - 전환선/기준선 크로스오버
  - Chikou Span 확인

### 📰 뉴스 기능
- 각 Top5 종목별 **실시간 뉴스** 수집
- NewsAPI 통합 (1.5초 rate limiting)
- 클릭 가능한 뉴스 링크

### 🔧 추가 기능
- **섹터 모멘텀** 보너스
- **실적 리스크** 필터링 (±5 포인트)
- **ATR 변동성** 필터 (5% 달성 가능성 검증)
- **시장 레짐** 판단 (SAFE/CAUTION/RISK_OFF)

---

## 🚀 빠른 시작

### 1. 로컬 설치

```bash
# 저장소 클론
git clone https://github.com/your-username/us-stock-analyzer.git
cd us-stock-analyzer

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. 로컬 실행

```bash
# Streamlit 앱 실행
streamlit run app.py

# 브라우저에서 http://localhost:8501 접속
```

### 3. GitHub + Streamlit Cloud 배포 (모바일 접속 가능)

#### 단계 1: GitHub에 푸시
```bash
git add .
git commit -m "Add US Stock Analyzer"
git push origin main
```

#### 단계 2: Streamlit Cloud 배포
1. https://streamlit.io 접속
2. "Create app" 클릭
3. GitHub 계정 연결
4. Repository: `us-stock-analyzer` 선택
5. Main file: `app.py` 선택
6. **Deploy** 클릭

#### 단계 3: Secrets 설정 (배포된 앱에서)
Streamlit Cloud의 앱 설정 → Secrets:
```toml
NEWS_API_KEY = "your-api-key"
```

#### 단계 4: 완료! 🎉
```
https://your-username-us-stock-analyzer.streamlit.app
```

---

## 📱 모바일에서 접속

배포 후, 폰의 브라우저에서 위의 URL을 입력하면 즉시 사용 가능합니다.

**지원 기기:**
- ✅ iPhone / iPad (Safari)
- ✅ Android (Chrome)
- ✅ 데스크톱 (모든 브라우저)

---

## 🔧 설정

### .env 파일 설정

```env
# NewsAPI (https://newsapi.org)
NEWS_API_KEY=your-key-here

# Anthropic API (선택사항)
ANTHROPIC_API_KEY=your-key-here

# 분석 설정
ANALYSIS_PERIOD_DAYS=365
TOP_N_RECOMMENDATIONS=5
TARGET_GAIN_PERCENT=5.0
```

### config/settings.py

주요 설정:
- `TECHNICAL_WEIGHTS` - 기술 지표 가중치
- `ATR_FEASIBILITY_THRESHOLD_PCT` - 변동성 필터 (기본 2.5%)
- `EARNINGS_RISK_WINDOW_DAYS` - 실적 리스크 윈도우 (기본 7일)
- `SECTOR_MOMENTUM_MAX_BONUS` - 섹터 보너스 상한 (기본 5점)

---

## 📊 백테스트 결과

**2025-07-25 ~ 2026-07-25 (1년)**
```
분석 주간: 51
총 거래: 255
승률: 50.98%
누적 수익률: 28.12%

최고 주: 5.88% (Week 44)
최악 주: -1.82% (Week 49)
```

---

## 📋 리포트

### 마크다운 리포트 (`top5_recommendations_YYYY-MM-DD.md`)
- Top 5 종목별 상세 분석
- 기술 지표 점수 breakdown
- 뉴스 링크
- 면책 조항

### JSON 데이터 (`analysis_data_YYYY-MM-DD.json`)
- 전체 분석 결과
- 종목별 지표값
- 순위 정보

### 일일 캐시 (`data/cache/analysis_cache_YYYY-MM-DD_HHMM.json`)
- 분석 결과 캐싱 (24시간 유효)

---

## 🛠️ 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | Streamlit, HTML/CSS |
| Backend | Python 3.10+ |
| Data | pandas, numpy |
| Market Data | yfinance |
| Technical Analysis | ta (TA-Lib Python) |
| News | NewsAPI, requests |
| Visualization | Plotly |
| Deployment | GitHub + Streamlit Cloud |

---

## 📝 API 키 획득

### NewsAPI
1. https://newsapi.org 접속
2. 무료 가입 (이메일 필요)
3. API Key 복사
4. `.env` 파일에 붙여넣기

```env
NEWS_API_KEY=your-key-here
```

### Anthropic (선택사항)
1. https://console.anthropic.com 접속
2. API Key 생성
3. 환경 변수 설정

---

## 🧪 로컬 테스트

```bash
# 기본 테스트
python main.py --period-days 30

# 기술 분석만
python main.py --mode technical

# 특정 종목만 분석
python main.py --tickers AAPL MSFT NVDA

# 캐시 무시
python main.py --clear-cache

# 디버그 모드
python main.py --debug
```

---

## 📈 성능 최적화

- ✅ **병렬 처리** - 4개 워커로 종목 분석
- ✅ **캐싱** - 24시간 결과 캐싱
- ✅ **API 최적화** - Top5만 뉴스 검색 (95% 감소)
- ✅ **로그 억제** - yfinance 경고 제거
- ✅ **타임스탐프** - 분석 결과 추적 (YYYY-MM-DD_HHMM)

---

## ⚠️ 면책 조항

**본 분석은 정보 제공 목적이며 투자 조언이 아닙니다.**

- 과거 성과는 미래 결과를 보장하지 않습니다
- 항상 자신의 판단과 전문가 자문으로 투자 결정하세요
- 투자는 신중하게 결정하세요

---

## 🤝 기여

이슈 및 Pull Request는 언제든 환영합니다!

```bash
# Fork → Clone → Branch → Commit → Push → PR
git checkout -b feature/your-feature
git commit -am "Add your feature"
git push origin feature/your-feature
```

---

## 📄 라이선스

MIT License - 자유롭게 사용하세요

---

## 📞 지원

문제가 있으신가요?

1. **GitHub Issues** - 버그 리포트
2. **Discussions** - 질문 & 피드백
3. **Email** - [your-email@example.com]

---

## 🌟 로드맵

- [ ] Elliott Wave 지표 추가
- [ ] 일일 알림 기능 (Slack/이메일)
- [ ] 포트폴리오 추적
- [ ] 머신러닝 모델 통합
- [ ] 다국어 지원

---

## 📊 업데이트 로그

### v2.0 (2026-07-25)
- ✅ Ichimoku Cloud 지표 추가 (20%)
- ✅ Sentiment 분석 제거
- ✅ 실시간 뉴스 통합
- ✅ Streamlit 앱 완전 재구성
- ✅ Streamlit Cloud 배포 지원

### v1.0 (초기 버전)
- 5개 기술 지표
- 감성 분석 포함
- 로컬 실행만 지원

---

**Happy Analyzing! 📈**

