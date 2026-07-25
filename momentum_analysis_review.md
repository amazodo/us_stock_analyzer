# 📊 모멘텀 지표 분석 로직 검증 리포트

## 개요
requirements.md의 요구사항 대비 현재 구현된 모멘텀(Momentum) 분석 로직의 적합성을 검증합니다.

---

## 1. 요구사항 vs 구현 비교

### 📋 요구사항 (requirements.md 24~27줄)

```
#### 모멘텀 지표 (Momentum)
- RSI (14일): 과매수/과매도 판단
- MACD: 추세 전환 신호
- Stochastic: %K, %D 라인
```

### ✅ 구현 상태

| 지표 | 요구사항 | 구현 | 상태 |
|------|--------|------|------|
| **RSI 14** | ✓ | ✓ | ✅ |
| **MACD** | ✓ | ✓ | ✅ |
| **MACD Signal** | ✓ | ✓ | ✅ |
| **Stochastic %K** | ✓ | ✓ | ✅ |
| **Stochastic %D** | ✓ | ✓ | ✅ |

**결론**: 모든 기본 지표가 구현됨 ✅

---

## 2. 상세 구현 검증

### 2.1 RSI (Relative Strength Index) 계산

**코드 위치**: `src/indicators/momentum.py:14-38`

```python
delta = df[column].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
rs = gain / loss.replace(0, 1e-10)
df['RSI_{window}'] = 100 - (100 / (1 + rs))
```

**검증**:
- ✅ 표준 RSI 공식 정확
- ✅ 0으로 나누기 방지 (1e-10 대체)
- ✅ 14일 period 지원
- ✅ 간단한 이동평균 (SMA) 사용

**평가**: **적합** 🟢

**주의점**:
```
⚠️ 참고: Wilder's Smoothing vs Simple MA
- 현재: 간단한 이동평균 (SMA)
- 표준: Wilder's Smoothing (가중 이동평균)
- 영향도: 낮음 (최근값에 충분히 수렴)
```

---

### 2.2 MACD (Moving Average Convergence Divergence) 계산

**코드 위치**: `src/indicators/momentum.py:40-76`

```python
ema_fast = df[column].ewm(span=fast, adjust=False).mean()  # 12
ema_slow = df[column].ewm(span=slow, adjust=False).mean()  # 26
df['MACD'] = ema_fast - ema_slow
df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()  # 9
df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
```

**검증**:
- ✅ 표준 MACD 공식 정확 (12/26/9)
- ✅ EMA 사용 (지수가중 이동평균)
- ✅ `adjust=False` 설정 (맞음)
- ✅ Histogram 계산 포함

**평가**: **적합** 🟢

---

### 2.3 Stochastic Oscillator 계산

**코드 위치**: `src/indicators/momentum.py:78-112`

```python
low_min = df['Low'].rolling(window=k_period).min()
high_max = df['High'].rolling(window=k_period).max()
raw_k = 100 * (df['Close'] - low_min) / (high_max - low_min)
df['Stochastic_%K'] = raw_k.rolling(window=smooth_k).mean()
df['Stochastic_%D'] = df['Stochastic_%K'].rolling(window=d_period).mean()
```

**검증**:
- ✅ 표준 Stochastic 공식 정확
- ✅ %K = (Close - Low_14) / (High_14 - Low_14) × 100 (정확)
- ✅ %D = SMA(%K, 3) (정확)
- ✅ 0-100 범위 자동 정규화

**평가**: **적합** 🟢

---

## 3. 모멘텀 점수 계산 로직 검증

### 📋 요구사항 (requirements.md 55줄)

```
- RSI/MACD (20점)
```

### 코드 위치: `src/analysis/technical_score.py:85-126`

```python
def calculate_momentum_score(self, df: pd.DataFrame) -> float:
    score = 50.0  # Base score
    
    # RSI scoring
    if 30 < rsi < 70:      score += 10
    elif rsi < 30:         score += 20  # Oversold
    elif rsi > 70:         score -= 10  # Overbought
    
    # MACD scoring
    if macd > macd_signal: score += 15
    elif macd < macd_signal: score -= 15
    
    # MACD positive
    if macd > 0:           score += 10
    
    return min(100, max(0, score))
```

### 세부 검증

#### 1️⃣ RSI 점수 (+0~20점)

| 조건 | 추가점 | 설명 |
|------|--------|------|
| RSI 30-70 (중립) | +10 | 균형잡힌 상태 |
| RSI < 30 (과매도) | +20 | 반등 신호 (강세) |
| RSI > 70 (과매수) | -10 | 조정 신호 (약세) |

**분석**:
- ✅ 과매도 > 중립 > 과매수 구조
- ✅ 기술적으로 타당
- ⚠️ 과매수 시 감점이 적음 (-10만)

**평가**: **대체로 적합** 🟡

**개선 가능 사항**:
```
현재: RSI > 70 = -10점 (약세)
제안: RSI > 70 = -15점 (더 강한 약세 신호)
이유: RSI의 과매수 신호의 중요성이 과매도 신호(+20)만큼 커야 함
```

---

#### 2️⃣ MACD 크로스오버 (+15 또는 -15점)

| 조건 | 추가점 | 설명 |
|------|--------|------|
| MACD > Signal | +15 | 강한 매수 신호 |
| MACD < Signal | -15 | 강한 매도 신호 |

**분석**:
- ✅ 크로스오버 개념 정확
- ✅ 크로스오버는 가장 강한 MACD 신호
- ✅ 대칭적 가중치 (±15) 적절

**평가**: **적합** 🟢

---

#### 3️⃣ MACD Zero-Line Cross (+10점)

| 조건 | 추가점 | 설명 |
|------|--------|------|
| MACD > 0 (영선 위) | +10 | 추세 강화 신호 |

**분석**:
- ✅ MACD > 0은 강세 확인
- ✅ 크로스오버 다음의 2차 신호로 적절
- ⚠️ 음수일 때 감점 없음 (비대칭)

**평가**: **부분적 개선 필요** 🟡

**개선 가능 사항**:
```
현재: MACD > 0 = +10점
제안: MACD < 0일 때 -5점 추가 (약세 확인)
이유: 대칭성 및 신호 강화
```

---

#### 4️⃣ 최대 점수 계산

```
최고: 50 + 20 + 15 + 10 = 95점
최저: 50 - 10 - 15 = 25점
범위: 25~95점
```

**특이점**: 
- ✅ 범위가 0-100 내에서 합리적
- ✅ 최악의 경우도 25점 (완전히 부정적이지 않음)
- ⚠️ 대칭성이 완벽하지 않음

---

## 4. 신호 생성 메서드 검증

### 4.1 RSI Signal

**코드**: `src/indicators/momentum.py:115-135`

```python
if rsi_value < 30:
    return 'oversold'
elif rsi_value > 70:
    return 'overbought'
else:
    return 'neutral'
```

**평가**: ✅ **적합** (표준 RSI 신호)

---

### 4.2 MACD Signal

**코드**: `src/indicators/momentum.py:138-169`

```python
if prev_macd <= prev_signal and current_macd > current_signal:
    return 'buy'
elif prev_macd >= prev_signal and current_macd < current_signal:
    return 'sell'
else:
    return 'neutral'
```

**평가**: ✅ **적합** (정확한 크로스오버 감지)

---

### 4.3 Stochastic Signal

**코드**: `src/indicators/momentum.py:172-198`

```python
if k_value < 20:
    return 'oversold'
elif k_value > 80:
    return 'overbought'
else:
    return 'neutral'
```

**평가**: ✅ **적합** (표준 Stochastic 신호)

---

## 5. Stochastic 미사용 문제 🔴

### 📋 요구사항: Stochastic 포함

requirements.md는 Stochastic을 명시적으로 요구하지만, **점수 계산에 사용되지 않음**

**현재 코드**:
```python
def calculate_momentum_score(self, df: pd.DataFrame) -> float:
    # RSI 점수 + MACD 점수만 계산
    # Stochastic은 계산되지 않음 ❌
```

**영향**:
- ⚠️ 모멘텀 지표 20% 중 1/3이 미사용
- ⚠️ 추세 확인 신호 부족
- ⚠️ 단기 과매수/과매도 판단 기능 미실장

### 권고 개선안

```python
def calculate_momentum_score(self, df: pd.DataFrame) -> float:
    score = 50.0
    
    # RSI scoring (현재대로)
    if 30 < rsi < 70:
        score += 10
    elif rsi < 30:
        score += 20
    elif rsi > 70:
        score -= 15  # 개선: -10 → -15 (대칭성)
    
    # MACD scoring (현재대로)
    if macd > macd_signal:
        score += 15
    elif macd < macd_signal:
        score -= 15
    
    if macd > 0:
        score += 10
    elif macd < 0:  # 개선: 영선 아래 감점
        score -= 5
    
    # NEW: Stochastic scoring (추가)
    if 'Stochastic_%K' not in df.columns:
        df = MomentumIndicators.calculate_stochastic(df)
    
    stoch_k = df['Stochastic_%K'].iloc[-1]
    stoch_d = df['Stochastic_%D'].iloc[-1]
    
    # Stochastic crossover
    if pd.notna(stoch_k) and pd.notna(stoch_d):
        if stoch_k < 20:
            score += 10  # Oversold, 반등 신호
        elif stoch_k > 80:
            score -= 10  # Overbought, 조정 신호
        elif stoch_k > stoch_d:  # Crossover up
            score += 5   # Momentum shift
        elif stoch_k < stoch_d:  # Crossover down
            score -= 5   # Momentum loss
    
    return min(100, max(0, score))
```

---

## 6. 가중치 적용 검증

### 📋 요구사항 (requirements.md 55줄)

```
- RSI/MACD (20점)
```

### 코드 위치: `src/analysis/technical_score.py:341-401`

```python
overall_score = (
    ma_score * 0.30 +
    momentum_score * 0.20 +  # ✅ 20%
    volatility_score * 0.20 +
    volume_flow_score * 0.20 +
    fib_score * 0.10
)
```

**검증**:
- ✅ momentum_score가 20% 가중치로 적용됨
- ✅ 요구사항 준수

**평가**: **적합** 🟢

---

## 7. 최종 평가 및 권고사항

### ✅ 긍정적 평가

1. **지표 구현 완성도**: RSI, MACD, Stochastic 모두 정확하게 구현됨
2. **신호 생성**: 모든 지표의 신호 생성 로직이 타당함
3. **가중치**: 모멘텀 점수가 20%로 정확하게 적용됨
4. **안정성**: NaN 처리 및 에러 핸들링 충분함

### 🔴 개선 필요 사항

#### 1. **Stochastic 미사용 (높은 우선순위)**

**문제**: 지표는 구현되었으나 점수 계산에 미포함
```
현재: RSI + MACD만 사용
요구: RSI + MACD + Stochastic 모두
```

**권고**: 모멘텀 점수 계산에 Stochastic 추가 (+10점 항목)

#### 2. **대칭성 부족 (중간 우선순위)**

**현재 문제**:
```
RSI 과매수: -10점 (약함)
MACD 영선 아래: 감점 없음 (불완전)
```

**권고**:
```
RSI > 70: -15점 (과매도 +20과 대칭)
MACD < 0: -5점 (영선 위 +10과 대칭)
```

#### 3. **Stochastic 신호 개선 (낮은 우선순위)**

**추가 고려사항**:
```
- Stochastic 크로스오버 추가 (±5점)
- Stochastic 과매수/과매도 신호 (±10점)
```

---

## 8. 수정 코드 예시

### 즉시 적용 가능한 수정안

**파일**: `src/analysis/technical_score.py`

```python
def calculate_momentum_score(self, df: pd.DataFrame) -> float:
    """
    Score based on RSI, MACD, Stochastic momentum.
    개선: 대칭성 + Stochastic 추가
    """
    try:
        if 'RSI_14' not in df.columns:
            df = MomentumIndicators.calculate_rsi(df, window=14)
        if 'MACD' not in df.columns:
            df = MomentumIndicators.calculate_macd(df)
        if 'Stochastic_%K' not in df.columns:
            df = MomentumIndicators.calculate_stochastic(df)

        rsi = df['RSI_14'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        macd_signal = df['MACD_Signal'].iloc[-1]
        stoch_k = df['Stochastic_%K'].iloc[-1]
        stoch_d = df['Stochastic_%D'].iloc[-1]

        score = 50.0  # Base score

        # RSI scoring - 개선: 대칭성 강화
        if pd.notna(rsi):
            if 30 < rsi < 70:
                score += 10  # Neutral
            elif rsi < 30:
                score += 20  # Oversold (bullish)
            elif rsi > 70:
                score -= 15  # Overbought (bearish) - 개선: -10 → -15

        # MACD scoring - 개선: 영선 기준 추가
        if pd.notna(macd) and pd.notna(macd_signal):
            if macd > macd_signal:
                score += 15  # MACD above signal
            elif macd < macd_signal:
                score -= 15  # MACD below signal

            if macd > 0:
                score += 10  # MACD above zero line
            elif macd < 0:
                score -= 5   # MACD below zero line - 개선: 추가

        # NEW: Stochastic scoring - 추가
        if pd.notna(stoch_k):
            if stoch_k < 20:
                score += 10  # Oversold (bullish)
            elif stoch_k > 80:
                score -= 10  # Overbought (bearish)
            
            # Stochastic crossover (optional)
            if pd.notna(stoch_d):
                if stoch_k > stoch_d:
                    score += 5   # K above D (momentum)
                elif stoch_k < stoch_d:
                    score -= 5   # K below D (loss of momentum)

        return min(100, max(0, score))

    except Exception as e:
        logger.error(f"Error calculating momentum score: {e}")
        return 50.0
```

---

## 9. 요약 점수

| 항목 | 점수 | 코멘트 |
|------|------|--------|
| 기본 지표 구현 | 95/100 | RSI, MACD, Stochastic 모두 정확 |
| 점수 계산 로직 | 70/100 | RSI+MACD는 좋으나 Stochastic 미사용, 대칭성 부족 |
| 요구사항 준수 | 65/100 | Stochastic 미실장, 일부 대칭성 문제 |
| 신호 생성 | 90/100 | 정확하고 안정적 |
| **종합** | **80/100** | 🟡 **개선 필요** |

---

## 10. 개선 우선순위

1. **P0 (긴급)**: Stochastic 점수 계산 추가
2. **P1 (중요)**: RSI 과매수 감점 강화 (-15으로 변경)
3. **P1 (중요)**: MACD 영선 기준 감점 추가 (-5)
4. **P2 (선택)**: Stochastic 크로스오버 신호 추가

---

**작성일**: 2026-07-25  
**버전**: 1.0
