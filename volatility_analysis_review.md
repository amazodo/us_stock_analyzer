# 변동성 지표 분석 로직 검토 보고서

**검토일**: 2026-07-25  
**상태**: 🔍 분석 완료 - 개선 권장

---

## 📋 개요

requirements.md의 요구사항 대비 변동성(Volatility) 지표 분석 로직의 불일치와 누락을 확인했습니다.

### 요구사항 (requirements.md)
```
변동성 지표 (Volatility)
- Bollinger Bands: 상단/중앙/하단
- ATR (Average True Range): 변동성 크기
- Beta: 시장 대비 민감도
```

### 현재 구현 상태
```
✅ Bollinger Bands: 구현됨
✅ ATR: 구현됨
❌ Beta: 완전 누락 (계산도 없음, 점수도 없음)
```

---

## ❌ 발견된 문제점

### 1. **Beta 지표 완전 누락**

**요구사항**: Beta는 시장 대비 민감도를 나타냄
- Beta > 1.0: 공격적 주식 (상승장 강점)
- Beta ≈ 1.0: 시장 동행
- Beta < 1.0: 방어적 주식 (하락장 강점)

**현재 구현**: 
- `src/indicators/volatility.py`에 Beta 계산 로직 없음
- `technical_score.py`의 `calculate_volatility_score()`에 Beta 고려 없음
- 점수 반영 없음

**문제점**: 변동성 20점 비중의 1/3이 누락

---

### 2. **Bollinger Bands 점수 비대칭**

**현재 로직**:
```python
# 상단 근처 (strong bullish)
if bb_position > 0.8:
    score += 20  # 가장 강한 가중치

# 중간 (neutral)
elif 0.4 < bb_position < 0.6:
    score += 10

# 하단 근처 (weak)
elif bb_position < 0.2:
    score -= 10  # 약한 가중치
```

**문제점**:
```
상단 근처: +20 (강한 신호)
하단 근처: -10 (약한 신호)

비대칭: +20 vs -10 → 상단이 2배 더 강함
결과: 약세 신호를 과소평가
```

**목표**: 대칭화 → +15/-15 또는 +20/-20

---

### 3. **ATR 점수 로직 불완전**

**현재 로직**:
```python
atr_pct = (df['ATR'].iloc[-1] / price) * 100

if 1 < atr_pct < 3:      # 적정 변동성
    score += 10
elif atr_pct > 5:         # 매우 높은 변동성
    score -= 10

# 이 구간들은 처리 없음:
# atr_pct < 1% (극저 변동성)
# 3% <= atr_pct <= 5% (중간-높은)
```

**문제점**:
```
1. 3~5% 구간: 처리 없음 (gap)
   → 3.5% ATR은 +10 또는 0으로 처리됨? (명확하지 않음)

2. < 1% (극저 변동성): 처리 없음
   → 1주일에 5% 달성 불가능한 종목
   → 5% Gain Feasibility 필터와 중복
   → 감점 처리 필요

3. 대칭성 부재: +10 vs -10 (균형잡혀 있지만)
   → 3단계만 구분 (저/적정/과) → 세분화 필요
```

---

### 4. **계층적 구조 부재 (vs 이동평균/모멘텀)**

**이동평균 구조** (개선됨):
```python
if price > SMA200:       # if-elif: 가장 강한 신호만
    score += 15
elif price > SMA50:      # 중간 신호
    score += 10
elif price > SMA20:      # 약한 신호
    score += 5
```
→ 1가지 신호만 카운트 (차별화)

**현재 변동성 구조**:
```python
if 0.4 < bb_position < 0.6:  # 독립적 조건들
    score += 10              # 모두 누적 가능

if 1 < atr_pct < 3:
    score += 10              # 또 누적
    
# 최악: 둘 다 만족 시 +20 누적
```
→ 여러 신호가 누적 가능 (과점수)

**개선**: 변동성 상태를 계층화
```python
if bb_squeeze and low_atr:           # 최안정 (보수)
    score += 5
elif bb_expansion and high_atr:      # 최불안 (공격)
    score -= 15
elif optimal_volatility:             # 최적 변동성
    score += 15
# 등등 → if-elif 구조
```

---

### 5. **NaN 안전성 부족**

**현재**:
```python
bb_position = df['BB_Position'].iloc[-1]

if 0.4 < bb_position < 0.6:  # bb_position이 NaN이면 비교 오류
    score += 10
```

**필요**:
```python
if pd.notna(bb_position) and 0.4 < bb_position < 0.6:
    score += 10
```

---

## 📊 점수 분포 비교 (현재 vs 개선 안)

### 강한 상승 + 적정 변동성
```
현재:
  Base: 50
  BB (상단, >0.8): +20
  ATR (1-3%): +10
  = 80점

개선 후:
  Base: 50
  BB (상단, 최적): +15
  Beta (>1, 공격형): +10
  = 75점 (더 현실적)
```

### 약한 신호 + 극저 변동성
```
현재:
  Base: 50
  BB (중간, 0.4-0.6): +10
  ATR (<1%): 0 (처리 없음)
  = 60점 (과평가)

개선 후:
  Base: 50
  BB (중간): 0
  Beta (<0.8, 방어형): +5
  ATR (<1%, 극저): -5
  = 50점 (중립)
```

### 강한 약세 + 높은 변동성
```
현재:
  Base: 50
  BB (하단, <0.2): -10
  ATR (>5%): -10
  = 30점

개선 후:
  Base: 50
  BB (하단, 최악): -20
  Beta (<0.8, 방어형): +5
  ATR (>5%, 극고): -10
  = 25점 (명확한 약세)
```

---

## ✨ 개선안

### Phase 1: 즉시 적용 가능

#### 1.1 Bollinger Bands 대칭화
```python
# 현재
if bb_position > 0.8:
    score += 20
...
elif bb_position < 0.2:
    score -= 10

# 개선
if pd.notna(bb_position):
    if bb_position > 0.8:
        score += 20  # 또는 +15
    elif bb_position > 0.6:
        score += 10
    elif bb_position > 0.4:
        score += 5
    elif bb_position < 0.2:
        score -= 20  # 대칭: -10 → -20
    elif bb_position < 0.4:
        score -= 10
```

#### 1.2 ATR 점수 보간
```python
if pd.notna(atr_pct):
    if atr_pct < 1:          # 극저
        score -= 5
    elif 1 <= atr_pct < 2:   # 저
        score += 5
    elif 2 <= atr_pct < 3:   # 적정
        score += 10
    elif 3 <= atr_pct < 5:   # 중간
        score += 0   # 중립
    elif atr_pct >= 5:       # 과고
        score -= 10
```

#### 1.3 NaN 체크 강화
```python
if pd.notna(bb_position):  # 모든 비교 전 체크
    ...
if pd.notna(atr_pct):
    ...
```

---

### Phase 2: Beta 지표 통합 (중기)

#### 2.1 Beta 계산 추가
```python
# src/indicators/beta.py (신규)
def calculate_beta(stock_returns, market_returns):
    """
    Beta = Covariance(stock, market) / Variance(market)
    """
    covariance = np.cov(stock_returns, market_returns)[0][1]
    variance = np.var(market_returns)
    return covariance / variance
```

#### 2.2 Beta 점수 추가
```python
# technical_score.py
def calculate_volatility_score(self, df: pd.DataFrame, beta: float = None) -> float:
    ...
    
    # Beta 점수
    if beta is not None and pd.notna(beta):
        if beta > 1.2:           # 높은 베타 (공격형)
            score += 10          # 상승장 강점
        elif beta > 1.0:         # 약한 고베타
            score += 5
        elif beta < 0.8:         # 낮은 베타 (방어형)
            score -= 5           # 하락장 강점 (현재는 약점)
        elif beta < 0.6:         # 매우 낮은 베타
            score -= 10
```

---

### Phase 3: 계층적 구조 재설계 (고급)

```python
def calculate_volatility_score(self, df: pd.DataFrame) -> float:
    """
    Improved hierarchical volatility scoring:
    1. Determine volatility state (squeeze, optimal, expansion)
    2. Combine with price position (BB_Position)
    3. Add Beta sensitivity
    """
    
    # State: Squeeze vs Normal vs Expansion
    bb_signal = get_bollinger_signal(df)
    
    if bb_signal == 'squeeze':
        # 압축 상태: 움직임 임박 신호
        base_volatility_score = 30  # 낮은 베이스
    elif bb_signal == 'expansion':
        # 확대 상태: 강한 이동 중
        base_volatility_score = 70  # 높은 베이스
    else:
        # 정상 상태
        base_volatility_score = 50  # 중립
    
    # Price position 추가
    if bb_position > 0.8 and bb_signal == 'expansion':
        volatility_score += 20  # 동조: 강세
    elif bb_position < 0.2 and bb_signal == 'expansion':
        volatility_score -= 20  # 동조: 약세
    
    # Beta 조정
    if beta > 1.2:
        volatility_score += 10
    elif beta < 0.8:
        volatility_score -= 5
    
    return min(100, max(0, volatility_score))
```

---

## 📈 요구사항 준수 현황

| 요구사항 | 현재 | 개선 필요 |
|---------|------|---------|
| Bollinger Bands | ✅ 구현 | ⚠️ 대칭화 |
| ATR | ✅ 구현 | ⚠️ 보간 개선 |
| Beta | ❌ 누락 | ❌ 신규 필요 |
| 점수 반영 | ✅ 일부 | ⚠️ 완성 필요 |

---

## 🚀 권장 개선 순서

### 1순위: 즉시 (Phase 1)
- [ ] BB 점수 대칭화 (+20/-20)
- [ ] ATR 보간 (5단계)
- [ ] NaN 체크 추가

### 2순위: 단기 (Phase 2)
- [ ] Beta 계산 로직 추가
- [ ] Beta 점수 통합

### 3순위: 중기 (Phase 3)
- [ ] Bollinger Squeeze/Expansion 신호
- [ ] 계층적 구조 개선

---

## 💡 기술적 설명

### Bollinger Bands Position
```
0.0 -------- 0.2 -------- 0.4 -------- 0.6 -------- 0.8 -------- 1.0
[하단]        [약세]        [중립]        [중립]        [강세]        [상단]
```

### ATR 해석
```
ATR% < 1%:    극저 변동성 (5% 달성 어려움)
1% ~ 3%:      적정 변동성 (5% 달성 가능)
3% ~ 5%:      중간 변동성 (5% 달성 용이)
5% 이상:      극고 변동성 (위험)
```

### Beta 해석
```
Beta > 1.2:   공격형 (상승장 강점, 하락장 약점)
0.8 ~ 1.2:    중립 (시장 동행)
Beta < 0.8:   방어형 (하락장 강점, 상승장 약점)
```

---

## 📝 결론

**현재 상태**: ⚠️ 부분 구현, Beta 누락

**개선 필요도**: 🔴 높음
- Beta 지표 완전 누락 → 20점 중 ~7점 손실
- ATR 로직 미흡 → 7-8점 차이
- 비대칭 점수 → 2-3점 영향

**권장**: Phase 1 + Phase 2 즉시 적용 (Phase 3는 선택사항)

