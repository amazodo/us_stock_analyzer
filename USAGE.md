# 실행 가이드 — Top5 정확도 개선 (Market/Sector 리스크 분석)

## 한 줄 요약
**기술지표 + 뉴스감성 + 실적리스크 + 섹터모멘텀 + 시장레짐 을 종합해 Top5 추천**

---

## 빠른 실행

### 1. 기본 실행 (기본값: S&P 100, 60일 분석)
```bash
python main.py
```
**출력:**
- 터미널: Top 5 추천 목록
- `outputs/` 폴더: Markdown 리포트 + JSON 데이터

---

### 2. 커스텀 티커 지정
```bash
python main.py --tickers AAPL MSFT GOOGL NVDA TSLA TSLA XOM JNJ
```
**주의:** 띄어쓰기로 구분

---

### 3. 분석 기간 변경 (기본값: 60일)
```bash
python main.py --period-days 90
```

---

### 4. 조합 사용
```bash
python main.py --tickers AAPL MSFT NVDA --period-days 30
```

---

## 구현된 4가지 개선 요인

### Phase 1: 실적 발표 리스크 ⚠️
- **기능:** 향후 7일 내 실적 발표 예정 종목 감점
- **영향:** -5점 (ensemble score 단계에서)
- **UI에서:** `earnings_warning` 필드에 날짜 표시

### Phase 2: 섹터 모멘텀 📊
- **기능:** 섹터 상대강도 계산 (상위 섹터 보너스, 하위 섹터 페널티)
- **영향:** ±5점
- **예시:**
  - Technology 강세 → NVDA, MSFT: +5점
  - Consumer Cyclical 약세 → TSLA: -5점

### Phase 3: Beta 기반 변동성 조정 📈
- **기능:** 고베타 공격주 vs 저베타 방어주 점수 차등
- **영향:** ±10점 (volatility_score 단계)
- **예시:**
  - NVDA (β=1.8) vs KO (β=0.7) 변동성 차이 반영

### Phase 4: 시장 레짐 배지 🎯
- **기능:** 현재 시장 상황 판정 (Safe/Caution/Risk-Off)
- **판정 기준:**
  - **Safe:** SPY·QQQ 모두 MA20 상회, VIX < 20
  - **Caution:** VIX 20~30 또는 하나 아래
  - **Risk-Off:** VIX ≥ 30 또는 둘 다 아래
- **영향:** Top5 순위 미변경 (컨텍스트 정보)

---

## 출력 해석

### 터미널 (Top 5)
```
#1. NVDA     | Score:   61.6/100 | Tech:   61.0 | Sent:   50.0
#2. MSFT     | Score:   57.1/100 | Tech:   53.5 | Sent:   50.0
#3. GOOGL    | Score:   43.5/100 | Tech:   47.5 | Sent:   50.0
```

- **Score:** 최종 점수 (기술 60% + 감성 40% + 섹터보너스 ± 실적감점)
- **Tech:** 기술 지표 점수 (MA 30% + 모멘텀 20% + 변동성 20% + 거래량 20% + 피보나치 10%)
- **Sent:** 뉴스 감성 점수

### Market Regime (예시)
```
Market regime: RISK_OFF — Both SPY and QQQ below 20-day moving average
```
→ "지금은 방어적 포지션 추천" 신호

### JSON 데이터 (`outputs/analysis_data_*.json`)
```json
{
  "market_regime": {
    "regime": "risk_off",
    "spy_signal": false,
    "qqq_signal": false,
    "vix_level": 22.5
  },
  "sector_bonuses": {
    "NVDA": 5.0,
    "MSFT": 5.0,
    "GOOGL": -5.0
  },
  "earnings_risk_data": {
    "AAPL": {"within_risk_window": false},
    "TSLA": {"within_risk_window": true, "next_earnings_date": "2026-08-01"}
  }
}
```

---

## 테스트

### 단위 테스트
```bash
python test_integration.py
```
- ✅ 8개 기술 지표 검증
- ✅ 감성 분석 검증
- ✅ 순위 시스템 검증

### 빠른 테스트 (20종목)
```bash
python quick_top3_test.py
```

### 5년 백테스트 (시간 소요 ~5분)
```bash
python backtest_top3_analysis.py
```

---

## 설정 변경

### `config/settings.py`
```python
# 실적 리스크
EARNINGS_RISK_WINDOW_DAYS = 7        # 발표 임박 기간 (일)
EARNINGS_RISK_PENALTY_POINTS = 5.0   # 감점 크기

# 섹터 모멘텀
SECTOR_MOMENTUM_MAX_BONUS = 5.0       # 보너스 상한
SECTOR_MOMENTUM_LOOKBACK_DAYS = 20    # 계산 기간

# 시장 레짐
MARKET_REGIME_MA_PERIOD = 20          # 이동평균 기간
VIX_CAUTION_LEVEL = 20                # Caution 임계치
VIX_RISK_OFF_LEVEL = 30               # Risk-Off 임계치
```

---

## 주의사항

1. **뉴스 API 필수:** `.env`에 `NEWS_API_KEY` 설정 필요 (없으면 감성 = 중립)
2. **Claude API 선택:** `.env`에 `ANTHROPIC_API_KEY` 있으면 전문가 의견 포함
3. **데이터 지연:** yfinance 조회 시간 ~1-2초/종목
4. **시장 종료 후:** 장시간 후 실행 시 당일 데이터 미반영 (전날 기준)

---

## 예시

### 약세장 시나리오
```bash
$ python main.py --tickers AAPL MSFT JNJ DUK KO

Market regime: RISK_OFF — VIX: 28.5

#1. JNJ   | Score: 52.1/100  (저베타, 방어주)
#2. DUK   | Score: 51.3/100  (공익사, 안정)
#3. KO    | Score: 48.7/100  (방어주)
#4. MSFT  | Score: 45.2/100  (고베타, 기술)
#5. AAPL  | Score: 43.8/100  (고베타, 기술)
```
→ 약세장에서 섹터보너스·베타 조정으로 방어주 상승

### 강세장 시나리오
```bash
$ python main.py --tickers AAPL MSFT NVDA TSLA GOOGL

Market regime: SAFE — SPY: 750.2 > MA20: 745.5, QQQ: 685.1 > MA20: 680.3

#1. NVDA  | Score: 68.2/100  (고베타, 기술 강세)
#2. MSFT  | Score: 64.5/100  (고베타, 기술 강세)
#3. GOOGL | Score: 52.3/100  (중베타, 통신)
#4. TSLA  | Score: 48.1/100  (고베타)
#5. AAPL  | Score: 47.9/100  (중베타)
```
→ 강세장에서 고베타·기술주 상승

---

## 추가 정보

- **더 보기:** `requirements.md` (요구사항)
- **기술 상세:** `src/analysis/` 각 모듈 주석 참고
- **문제 해결:** `logs/` 폴더의 상세 로그 확인
