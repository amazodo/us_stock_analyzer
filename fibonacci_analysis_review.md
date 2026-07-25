# 피보나치 지표 분석 로직 검토 보고서

**검토일**: 2026-07-25  
**상태**: 🔍 분석 완료 - 개선 권장

---

## 📋 개요

requirements.md의 요구사항 대비 피보나치(Fibonacci Retracement) 분석 로직의 불일치와 미활용을 확인했습니다.

### 요구사항 (requirements.md)
```
피보나치 분석 (Fibonacci Retracement)
- 최근 상승/하락 구간에서 38.2%, 50%, 61.8% 지지/저항 수준 계산
- 스윙 고점/저점 기반 계산

정량 점수 비중: 10점 (정량 점수의 10%)
```

### 현재 구현 상태
```
✅ 계산: 스윙 고점/저점 기반 피보나치 레벨 계산 완벽
✅ 38.2%, 61.8%: 점수에 반영됨
❌ 50% 수준: 계산되지만 점수에 미반영
❌ 역추세 신호: 반전 신호 누락
❌ 확장 수준: 161.8% 계산되지만 미사용
```

---

## ❌ 발견된 문제점

### 1. **50% 수준 미사용 (요구사항 위반)**

**요구사항**: "38.2%, 50%, 61.8% 지지/저항 수준"

**현재 구현**:
```python
level_618 = levels.get('61.8%', current_price)
level_382 = levels.get('38.2%', current_price)
level_236 = levels.get('23.6%', current_price)  # ← 50% 대신 23.6% 사용

if current_price > level_618:
    score += 20
elif current_price > level_382:
    score += 10
elif current_price > level_236:  # ← 23.6% (요구사항과 다름)
    score += 5
```

**문제점**:
- 50% 수준 계산되지만 사용 안 됨
- 23.6% 수준 사용 (요구사항 위반)
- 50%는 심리적 중점 → 전략적으로 중요

---

### 2. **비대칭 점수 구조**

**현재 로직**:
```python
if current_price > level_618:      # 상단
    score += 20
elif current_price > level_382:
    score += 10
elif current_price > level_236:
    score += 5
else:                              # 하단 (모두 낮음)
    score -= 10
```

**문제점**:
```
상단 근처: 최대 +20
하단 근처: 최대 -10 (비대칭, 2배 약함)

결과: 약세 신호 과소평가
```

**개선**: 대칭화 → +20/-20 또는 +15/-15

---

### 3. **역추세(반전) 신호 누락**

**현재**: 가격이 낮은 수준 → 단순히 -10점

**개선안**: 
```
가격이 극저 수준(23.6% 이하)
  → 과도 매도 상태 (반전 신호!)
  → 보상 점수 필요

예시:
- 가격 < 23.6%: 과도 매도 (-20 대신 +10)
- 가격이 50%에서 상향 돌파: +15 (중요 지지 이탈)
- 가격이 61.8% 하향 이탈: -15 (주요 저항 돌파)
```

---

### 4. **Trend 감지 약함**

**현재**:
```python
if high_idx > low_idx:  # High is more recent (downtrend)
    levels = calculate_downtrend_retracement(...)
else:  # Low is more recent (uptrend)
    levels = calculate_uptrend_retracement(...)
```

**문제점**:
- Trend 정보가 score 계산에 미반영
- 상승추세인데 가격이 낮은 수준 = 좋은 매수 신호
- 하락추세인데 가격이 높은 수준 = 나쁜 신호
- 차별화 필요

---

### 5. **확장 수준 미사용**

**현재**:
```python
# calculate_extended_levels() 함수는 존재하지만
# analyze_fibonacci()에서 호출되지 않음
# score 계산에도 반영 안 됨

extension = {
    '161.8% Extension': 계산됨 (사용 안 함)
    '200% Extension': 계산됨 (사용 안 함)
}
```

**활용 기회**:
```
가격이 확장 수준 넘어섬 = 매우 강한 추세
→ +10점 보너스 가능
```

---

### 6. **NaN 체크 및 경계 처리 미흡**

**현재**:
```python
current_price = fib_analysis.get('current_price', 0)
levels = fib_analysis.get('retracement_levels', {})

if not levels:
    return 50.0

# levels에서 직접 get (없으면 current_price로 기본값)
level_618 = levels.get('61.8%', current_price)
```

**문제점**:
- `analyze_fibonacci()` 반환값이 빈 dict일 수 있음 (스윙 감지 실패)
- levels가 있어도 특정 키가 없을 수 있음
- current_price = 0 처리 미흡

---

## 📊 점수 분포 비교 (현재 vs 개선 안)

### 강한 상승추세 + 상단 근처
```
현재:
  Base: 50
  Price > 61.8%: +20
  = 70점

개선 후:
  Base: 50
  Uptrend detected: 0
  Price > 61.8% (상단): +15
  = 65점 (더 현실적)
```

### 상승추세 중 50% 반전 테스트
```
현재:
  Base: 50
  Price at 50% level: 0 (처리 안 함)
  = 50점 (기회 놓침)

개선 후:
  Base: 50
  Uptrend + at 50% (중요 지지): +10
  = 60점 (매수 신호 포착)
```

### 극저 수준 + 과도매도
```
현재:
  Base: 50
  Price < 23.6%: -10 (약세)
  = 40점

개선 후:
  Base: 50
  Downtrend + at <23.6% (반전 신호): +10
  = 60점 (명확한 반전 신호)
```

### 강한 하락추세 + 저점 근처
```
현재:
  Base: 50
  Price < 23.6%: -10
  = 40점

개선 후:
  Base: 50
  Downtrend + at <23.6% (반전 기대): +10
  Price < 0% (스윙저 아래): -20 (계속 약세)
  = 40점 (구분 가능)
```

---

## ✨ 개선안

### Phase 1: 즉시 적용 (요구사항 준수)

#### 1.1 50% 수준 추가
```python
level_618 = levels.get('61.8%', current_price)
level_500 = levels.get('50%', current_price)     # NEW
level_382 = levels.get('38.2%', current_price)

if current_price > level_618:
    score += 20
elif current_price > level_500:  # NEW
    score += 10
elif current_price > level_382:
    score += 5
else:
    score -= 10
```

#### 1.2 점수 대칭화
```python
else:  # current_price <= level_382
    score -= 20  # -10 → -20 (대칭)
```

#### 1.3 Trend 정보 활용
```python
fib_analysis = analyze_fibonacci(df)
trend_direction = 'downtrend' if fib_analysis.get('trend') == 'down' else 'uptrend'

# Trend와 가격 위치의 조합으로 신호 강화
if trend_direction == 'uptrend' and current_price < level_382:
    # 상승추세 중 매수 기회
    score += 5
```

#### 1.4 NaN 안전성
```python
if pd.notna(current_price) and levels:
    ...
```

---

### Phase 2: 반전 신호 추가 (중기)

#### 2.1 극저 수준 반전 신호
```python
level_236 = levels.get('23.6%', current_price)
level_000 = min(levels.values()) if levels else current_price  # Swing Low

if current_price < level_236:
    # 과도매도 상태
    if current_price > level_000:
        score += 10  # 반전 신호 (스윙저 위)
    else:
        score -= 20  # 극도의 약세 (스윙저 이탈)
```

#### 2.2 50% 돌파 신호
```python
# 가격이 50% 수준을 넘을 때 추가 신호
if current_price > level_500 and trend_direction == 'uptrend':
    score += 5  # 중요 심리 수준 돌파
```

---

### Phase 3: 확장 수준 (선택사항)

#### 3.1 확장 수준 계산 및 활용
```python
extended_levels = FibonacciAnalysis.calculate_extended_levels(high_price, low_price)

if current_price > 1.618 * (high_price - low_price):
    score += 10  # 매우 강한 추세
```

---

## 📈 요구사항 준수 현황

| 요구사항 | 현재 | 개선 필요 |
|---------|------|---------|
| 38.2%, 50%, 61.8% 계산 | ✅ 계산됨 | ⚠️ 50% 점수 미반영 |
| 스윙 고점/저점 기반 | ✅ 구현 | ✅ (유지) |
| 점수 반영 (10점) | ✅ 부분 | ⚠️ 완성 필요 |
| 반전 신호 | ❌ 누락 | ❌ 신규 필요 |

---

## 🔄 개선 효과

### 현재 vs 개선 후

| 시나리오 | 현재 | 개선 | 차이 | 해석 |
|---------|------|------|------|------|
| 상승추세, 61.8% 위 | 70 | 65 | -5 | 더 현실적 |
| 상승추세, 50% | 50 | 60 | +10 | 매수신호 추가 |
| 상승추세, 23.6% (반전) | 40 | 60 | +20 | 반전신호 포착 |
| 하락추세, 23.6% 아래 | 40 | 30 | -10 | 계속약세 구분 |
| 극저 (스윙저 이탈) | 40 | 30 | -10 | 더 명확한 신호 |

---

## 📝 결론

**현재 상태**: ⚠️ 부분 구현, 50% 미반영, 반전신호 누락

**개선 필요도**: 🔴 높음
- 50% 수준 미사용 → 요구사항 위반 (10점 중 ~3점 손실)
- 반전 신호 누락 → 매수 기회 미포착
- 비대칭 점수 → 약세 신호 약함

**권장**: Phase 1 + Phase 2 즉시 적용 (Phase 3는 선택사항)

---

## 💡 피보나치 수준의 전략적 의미

### 가격이 각 수준에 있을 때 의미

```
가격 > 61.8%:  
  = 주요 저항 돌파, 강세
  = 상승추세 재개 신호

가격 @ 50%:
  = 심리적 중점
  = 지지/저항 가능성 높음
  = 추세 유지/반전 결정점

가격 @ 38.2%:
  = 주요 지지 수준
  = 강한 반전 가능성

가격 < 23.6%:
  = 극도의 약세
  = 과도매도 (반전 신호)
  = 또는 추세 연속 (추세 확인 필요)
```

---

## 🚀 권장 개선 순서

### 1순위: 즉시 (Phase 1)
- [ ] 50% 수준 추가
- [ ] 점수 대칭화 (+20/-20)
- [ ] Trend 정보 활용
- [ ] NaN 체크 추가

### 2순위: 단기 (Phase 2)
- [ ] 반전 신호 추가
- [ ] 극저 수준 구분

### 3순위: 선택 (Phase 3)
- [ ] 확장 수준 활용

