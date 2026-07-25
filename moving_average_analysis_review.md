# 📊 이동평균 분석 로직 검증 리포트

## 개요
requirements.md의 요구사항 대비 현재 구현된 이동평균(Moving Average) 분석 로직의 적합성을 검증합니다.

---

## 1. 요구사항 vs 구현 비교

### 📋 요구사항 (requirements.md 19~22줄)

```
#### 이동평균 (Moving Averages)
- SMA (Simple Moving Average): 20일, 50일, 200일
- EMA (Exponential Moving Average): 12일, 26일
- VWAP (Volume Weighted Average Price)
```

### ✅ 구현 상태

| 지표 | 요구사항 | 구현 | 상태 |
|------|--------|------|------|
| **SMA 20** | ✓ | ✓ | ✅ |
| **SMA 50** | ✓ | ✓ | ✅ |
| **SMA 200** | ✓ | ✓ | ✅ |
| **EMA 12** | ✓ | ✓ | ✅ |
| **EMA 26** | ✓ | ✓ | ✅ |
| **VWAP** | ✓ | ✓ | ✅ |

**결론**: 모든 기본 지표가 구현됨 ✅

---

## 2. 상세 구현 검증

### 2.1 SMA (Simple Moving Average) 계산

**코드 위치**: `src/indicators/moving_averages.py:14-29`

```python
df[f'SMA_{window}'] = df[column].rolling(window=window).mean()
```

**검증**:
- ✅ pandas `rolling().mean()` 사용 (표준 구현)
- ✅ 20, 50, 200 period 모두 지원
- ✅ 데이터 부족 시 NaN 자동 처리

**평가**: **적합** 🟢

---

### 2.2 EMA (Exponential Moving Average) 계산

**코드 위치**: `src/indicators/moving_averages.py:32-46`

```python
df[f'EMA_{window}'] = df[column].ewm(span=window, adjust=False).mean()
```

**검증**:
- ✅ pandas `ewm()` 사용 (표준 구현)
- ✅ `adjust=False` 사용 → 현재까지의 데이터로만 계산 (맞음)
- ✅ span parameter 정확 (window와 동일)

**평가**: **적합** 🟢

---

### 2.3 VWAP (Volume Weighted Average Price) 계산

**코드 위치**: `src/indicators/moving_averages.py:49-67`

```python
tp = (df['High'] + df['Low'] + df['Close']) / 3
df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
```

**검증**:
- ✅ Typical Price (TP) = (H + L + C) / 3 (표준 공식)
- ✅ 누적 합계 사용: Σ(TP × Volume) / Σ(Volume) (정확)
- ✅ 누적 방식 → 전체 기간의 누적 평균 (맞음)

**평가**: **적합** 🟢

---

## 3. 이동평균 점수 계산 로직 검증

### 📋 요구사항 (requirements.md 54줄)

```
- 이동평균 추세 (30점)
```

### 코드 위치: `src/analysis/technical_score.py:24-74`

```python
def calculate_moving_average_score(self, df: pd.DataFrame) -> float:
    # ...
    score = 50.0  # Base score
    
    # Price position relative to averages (+10 each)
    if latest_price > sma_20:      score += 10  # +10
    if latest_price > sma_50:      score += 10  # +10
    if latest_price > sma_200:     score += 10  # +10
    
    # MA alignment bullish (+20)
    if sma_20 > sma_50 > sma_200:  score += 20  # +20
    
    # EMA alignment (+10)
    if ema_12 > ema_26:            score += 10  # +10
    
    return min(100, max(0, score))
```

### 세부 검증

#### 1️⃣ 기본 점수 (Base Score) = 50점

| 조건 | 설명 | 평가 |
|------|------|------|
| `score = 50.0` | 중립점 | ✅ 적합 |

**의견**: 중립 상태를 50점으로 설정한 것은 표준적임 ✅

---

#### 2️⃣ 가격 대비 이동평균 (+0~30점)

| 조건 | 추가점 | 누적 | 설명 |
|------|--------|------|------|
| 가격 > SMA20 | +10 | 60 | 단기 상승추세 |
| 가격 > SMA50 | +10 | 70 | 중기 상승추세 |
| 가격 > SMA200 | +10 | 80 | 장기 상승추세 |

**분석**:
- ✅ 단기(20일) → 중기(50일) → 장기(200일)로 확장하며 강도 판단
- ✅ 모든 조건 만족 시 최대 80점 도달

**평가**: **적합** 🟢

**단, 주의점**:
```
🟡 잠재적 문제: 세 조건은 배타적이지 않음
- 예: 가격 > 200 이면, 일반적으로 가격 > 50, 가격 > 20도 동시 만족
- 즉, 거의 항상 +30점이 누적됨 (차별화 낮음)
```

---

#### 3️⃣ 이동평균 정렬 (MA Alignment) (+20점)

| 조건 | 추가점 | 설명 |
|------|--------|------|
| SMA20 > SMA50 > SMA200 | +20 | 강한 상승추세 신호 |

**분석**:
- ✅ 기술적으로 가장 강한 상승신호 (황금교차)
- ✅ 단기 > 중기 > 장기 순서가 정렬됨

**평가**: **적합** 🟢

---

#### 4️⃣ EMA 정렬 (+10점)

| 조건 | 추가점 | 설명 |
|------|--------|------|
| EMA12 > EMA26 | +10 | 단기 모멘텀 상승 |

**분석**:
- ✅ MACD 개념 (12 - 26 선)과 유사
- ✅ 빠른 반응성 (지수가중) 반영

**평가**: **적합** 🟢

---

## 4. 가중치 적용 검증

### 📋 요구사항 (requirements.md 188~191줄)

```
점수산정: 사용자가 선택한 기법들의 점수를 정규화 합산:
최종 점수 = (선택된 기술/수급 지표 점수 * 0.6) + (뉴스 감성 점수 * 0.4) + (섹터 모멘텀 가산점)
```

그리고 정량 점수 내 가중치:
```
- 이동평균 추세 (30점)
- RSI/MACD (20점)
- 변동성 (20점)
- 거래량/수급 (20점)
- 피보나치 (10점)
```

### 코드 위치: `src/analysis/technical_score.py:307-350` (calculate_overall_technical_score)

```python
overall_score = (
    ma_score * 0.30 +           # 이동평균 30%
    momentum_score * 0.20 +     # 모멘텀 20%
    volatility_score * 0.15 +   # 변동성 15% ❌
    volume_flow_score * 0.20 +  # 거래량 20%
    fib_score * 0.10 +          # 피보나치 10%
    supply_demand * 0.15        # 수급 15% ❌
)
```

### 🔴 **불일치 발견!**

| 요소 | 요구사항 | 구현 | 상태 |
|------|--------|------|------|
| 이동평균 | 30% | 30% | ✅ |
| RSI/MACD | 20% | 20% | ✅ |
| 변동성 | 20% | **15%** | ❌ |
| 거래량/수급 | 20% | **20%** (combined) | ⚠️ |
| 피보나치 | 10% | 10% | ✅ |
| **합계** | **100%** | **110%** | ❌ |

**문제**: 
- 변동성이 15%로 구현됨 (요구사항: 20%)
- supply_demand가 별도로 15%로 적용됨
- **총합이 110%** (100% 초과)

---

## 5. 최종 평가 및 권고사항

### ✅ 긍정적 평가

1. **기본 지표 완성도**: SMA, EMA, VWAP 모두 정확하게 구현됨
2. **점수 계산 로직**: 이동평균 기반 스코어링이 기술적으로 타당함
3. **데이터 처리**: 부족한 데이터에 대한 graceful handling
4. **표준화**: pandas 표준 함수 사용 (유지보수 용이)

### 🔴 개선 필요 사항

#### 1. 가중치 재조정 (높은 우선순위)

**현재 문제**:
```
변동성: 15% (요구: 20%)
수급: 15% (독립적 항목)
합계: 110% (초과)
```

**권고 변경안**:
```python
# 방안 A: 정확한 가중치 적용
overall_score = (
    ma_score * 0.30 +          # 이동평균 30%
    momentum_score * 0.20 +    # 모멘텀 20%
    volatility_score * 0.20 +  # 변동성 20% ✅
    volume_flow_score * 0.20 + # 거래량&수급 20% (통합)
    fib_score * 0.10           # 피보나치 10%
)
# 합계: 100%
```

**또는 방안 B: 공식대로 분리 (더 정밀)**:
```python
# 거래량 10% + 수급 10% = 20%로 분리
overall_score = (
    ma_score * 0.30 +
    momentum_score * 0.20 +
    volatility_score * 0.20 +
    volume_score * 0.10 +      # OBV만 계산
    supply_demand_score * 0.10 +  # VWAP, Spike만
    fib_score * 0.10
)
```

#### 2. 점수 편향성 (중간 우선순위)

**문제**: 가격이 큰 이동평균들을 모두 상회할 가능성이 높으면 점수가 과하게 높아짐

**예시**:
```
- 가격 > SMA200이면, 거의 항상 가격 > SMA50, 가격 > SMA20도 만족
- 결과: 항상 +30점이 자동 누적
- → 점수의 차별화 낮음
```

**개선 방안**:
```python
# 개선된 로직: 가장 높은 것만 카운트 (논리적)
score = 50.0

# 방안 1: 가장 강한 신호 하나만 선택
if latest_price > sma_200:
    score += 20  # 장기 강세
elif latest_price > sma_50:
    score += 15  # 중기 강세
elif latest_price > sma_20:
    score += 10  # 단기 강세

# MA 얼라인먼트는 별도
if sma_20 > sma_50 > sma_200:
    score += 10
```

또는 **방안 2: 거리 기반 (더 정밀)**:
```python
# 가격이 SMA로부터 얼마나 멀리 있는가?
dist_200 = (latest_price - sma_200) / sma_200 * 100
score = 50 + min(20, dist_200 * 2)  # 거리에 비례한 점수
```

#### 3. EMA 추가 신호 (낮은 우선순위)

**현재**: EMA12 > EMA26만 확인

**추천**: MACD 신호선도 함께 확인
```python
# 현재: EMA만
if ema_12 > ema_26:
    score += 10

# 개선: MACD 신호 추가 (이미 momentum.py에 있음)
# MACD > Signal Line 일 때 추가 가산
```

---

## 6. 수정 코드 예시

### 즉시 적용 가능한 수정안

**파일**: `src/analysis/technical_score.py`

```python
def calculate_moving_average_score(self, df: pd.DataFrame) -> float:
    """
    Score based on moving average trends.
    개선: 가중치 정확화 + 점수 편향성 개선
    """
    if len(df) < 200:
        return 50.0

    try:
        if 'SMA_20' not in df.columns:
            df = MovingAverageIndicators.calculate_multiple_smas(df, periods=[20, 50, 200])
        if 'EMA_12' not in df.columns:
            df = MovingAverageIndicators.calculate_multiple_emas(df, periods=[12, 26])

        latest_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]
        ema_12 = df['EMA_12'].iloc[-1]
        ema_26 = df['EMA_26'].iloc[-1]

        score = 50.0  # Base score

        # 개선 1: 계층적 가격 위치 (가장 높은 레벨만 카운트)
        if latest_price > sma_200:
            score += 15  # 장기 강세 신호
        elif latest_price > sma_50:
            score += 10  # 중기 강세 신호
        elif latest_price > sma_20:
            score += 5   # 단기 강세 신호

        # 개선 2: MA 정렬 (황금교차)
        if sma_20 > sma_50 > sma_200:
            score += 15  # 가중치 조정

        # EMA 정렬 (빠른 반응성)
        if ema_12 > ema_26:
            score += 10

        return min(100, max(0, score))

    except Exception as e:
        logger.error(f"Error calculating MA score: {e}")
        return 50.0
```

---

## 7. 요약 점수

| 항목 | 점수 | 코멘트 |
|------|------|--------|
| 기본 지표 구현 | 95/100 | SMA, EMA, VWAP 모두 정확 |
| 점수 계산 로직 | 70/100 | 로직은 타당하나 가중치 오류 |
| 요구사항 준수 | 60/100 | 가중치 100% 초과 문제 |
| 코드 품질 | 85/100 | 깔끔하나 편향성 있음 |
| **종합** | **77/100** | 🟡 **개선 필요** |

---

## 8. 개선 우선순위

1. **P0 (긴급)**: 가중치 재조정 (110% → 100%)
2. **P1 (중요)**: 점수 편향성 개선 (계층적 구조)
3. **P2 (선택)**: MACD 신호선 추가 확인

---

**작성일**: 2026-07-25  
**버전**: 1.0
