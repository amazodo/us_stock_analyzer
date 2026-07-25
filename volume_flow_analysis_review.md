# 거래량 & 수급 지표 분석 로직 검토 보고서

**검토일**: 2026-07-25  
**상태**: 🔍 분석 완료 - 개선 권장

---

## 📋 개요

requirements.md의 요구사항 대비 거래량 & 수급(Volume & Flow) 분석 로직의 미활용과 약점을 확인했습니다.

### 요구사항 (requirements.md)
```
거래량 & 수급 (Volume & Flow)
- OBV (On-Balance Volume): 누적 거래량 추세
- 수급 강도 추정: VWAP 대비 현재가, 거래량 급증, Volume Profile
- ATR 변동성 필터: 1주일 내 5% 달성 가능성 검증

정량 점수 비중: 20점 (거래량/수급 합쳐서)
```

### 현재 구현 상태
```
✅ OBV: 계산되지만 점수 반영 약함 (+10만)
✅ VWAP: 완벽히 구현됨
✅ Volume Spike: 감지되고 점수 있음 (+10)
❌ Volume Profile: 계산되지만 점수에 미반영
❌ MFI (Money Flow Index): 계산되지만 미사용
❌ AD_Line: 계산되지만 미사용
❌ Money Flow: 추정되지만 약함
```

---

## ❌ 발견된 문제점

### 1. **Volume Profile 완전 미사용**

**요구사항**: "Volume Profile(주요 매물대)을 통한 세력/기관 수급 유입 추정"

**현재 구현**:
```python
# calculate_volume_profile() 함수 존재 (행 81-130)
# 주요 거래량 가격대 파악 가능
# BUT: score 계산에 미반영

profile = analyzer.calculate_volume_profile(df)
# {
#   'bin_centers': [...],
#   'bin_volumes': [...],
#   'peak_levels': [...],  # 거래가 많은 가격대
#   'current_price': ...
# }
```

**문제점**:
- 주요 매물대 감지 가능하지만 활용 안 됨
- 가격이 주요 매물대에 가까우면 저항/지지 신호
- 점수 2-3점 손실

---

### 2. **OBV 점수 로직 약함**

**현재 로직**:
```python
# OBV trend (단순 비교)
if len(df) > 20:
    obv_recent = df['OBV'].iloc[-5:].mean()
    obv_older = df['OBV'].iloc[-25:-5].mean()
    if obv_recent > obv_older:
        score += 10  # 단순히 +10
```

**문제점**:
```
1. 상승이면 +10만 → 강도 측정 없음
2. OBV 낙하면 점수 0 → 약세 신호 없음
3. OBV 추세와 가격 동행성 미반영
```

**개선**: OBV 강도 측정 필요
```
OBV 강하게 상승: +15
OBV 약하게 상승: +5
OBV 약하게 하락: -5
OBV 강하게 하락: -15
```

---

### 3. **MFI (Money Flow Index) 완전 누락**

**요구사항**: "거래량 급증을 통한 기관 수급 유입 추정"

**현재 상태**:
```python
# calculate_money_flow_index()는 있지만
# 1. 계산되지 않음
# 2. 점수에 미반영

# MFI는 거래액 기반 추세 강도 지표
# - MFI > 80: 과매수
# - MFI < 20: 과매도
# - MFI 추세: 거래액 기반 모멘텀
```

**문제점**:
- RSI보다 superior한 지표 미활용
- 거래액 기반 신호 누락
- 점수 2-3점 손실

---

### 4. **Accumulation/Distribution Line (AD_Line) 미사용**

**현재 상태**:
```python
# calculate_accumulation_distribution()는 있지만
# 점수에 미반영

# AD_Line의 의미:
# - 누적 거래 자금의 방향
# - 가격 상승 시 거래량 많으면 → 적립 (수급 좋음)
# - 가격 하락 시 거래량 많으면 → 방출 (수급 나쁨)
```

**문제점**:
- 거래액 기반 자금 흐름 미반영
- 가격과 거래량 동향성 미감지
- 점수 1-2점 손실

---

### 5. **비대칭 점수 구조**

**현재 로직**:
```python
# VWAP Position
if vwap_pos > 0.6:
    score += 15      # 상단
elif vwap_pos < 0.4:
    score -= 10      # 하단 (약함, 비대칭)

# Institutional Flow
if inst_flow > 0.3:
    score += 15      # 강한 매수
elif inst_flow < -0.3:
    score -= 15      # 강한 매도 (균형)
```

**문제점**:
```
VWAP: +15/-10 (비대칭, 2x 차이)
Institutional: +15/-15 (균형)
```

---

### 6. **Institutional Flow 임계값 높음**

**현재 로직**:
```python
if inst_flow > 0.3:
    score += 15      # 강한 신호 필요
elif inst_flow > 0.1:
    score += 5       # 약한 신호
elif inst_flow < -0.3:
    score -= 15
```

**문제점**:
```
0.3 임계값이 너무 높음
→ 기관 수급이 명확할 때만 카운트
→ 약한 수급 신호도 반영 필요 (0.1-0.2 구간)
```

---

### 7. **거래량 추세 분석 약함**

**현재**:
```python
# Volume Trend 계산
if volume_trend > 1.2:
    score += 15   # 50% 이상 높음
elif volume_trend > 1.0:
    score += 10   # 20% 이상 높음
# 음수 케이스 없음
```

**문제점**:
```
1. 거래량 감소 시 처리 없음
2. 가격 상승/하락과의 조합 미반영
3. "거래량 좋음" vs "거래량 없음" 구분만 함
```

---

### 8. **NaN 체크 및 경계 처리 미흡**

**현재**:
```python
vwap_pos = sd_analysis.get('vwap_position', 0.5)
if vwap_pos > 0.6:
    score += 15
# vwap_pos = None인 경우 0.5로 기본값
```

**문제점**:
- None/NaN 처리 미흡
- 데이터 부족 시 false signal 가능

---

## 📊 점수 분포 비교 (현재 vs 개선 안)

### 강한 수급 + 고거래량
```
현재:
  Base: 50
  VWAP > 0.6: +15
  Volume Spike: +10
  Inst Flow > 0.3: +15
  = 90점

개선 후:
  Base: 50
  VWAP > 0.6: +15 (동일)
  Volume Spike: +10 (동일)
  MFI > 80: +10 (NEW)
  Inst Flow > 0.2: +10 (조정)
  AD Trend: +5 (NEW)
  = 90점 (더 다층적)
```

### 약한 수급 + 거래량 감소
```
현재:
  Base: 50
  VWAP 0.4-0.6: 0
  Volume < avg: 0 (처리 안 함)
  = 50점 (구분 안 됨)

개선 후:
  Base: 50
  VWAP 0.4-0.6: 0 (중립)
  Volume < avg: -5 (NEW)
  OBV 약 하락: -5 (NEW)
  = 40점 (명확한 약세)
```

### 기관 매도
```
현재:
  Base: 50
  Inst Flow < -0.3: -15
  = 35점

개선 후:
  Base: 50
  Inst Flow < -0.2: -10 (임계값 조정)
  AD_Line 방출: -5 (NEW)
  MFI < 30: -10 (NEW)
  = 25점 (더 명확)
```

---

## ✨ 개선안

### Phase 1: 즉시 적용 (필수)

#### 1.1 OBV 점수 강화
```python
# 현재
if obv_recent > obv_older:
    score += 10

# 개선
obv_diff = obv_recent - obv_older
obv_strength = obv_diff / max(abs(obv_older), 1)  # 강도 측정

if obv_strength > 0.1:      # 강한 상승 (10% 이상)
    score += 15
elif obv_strength > 0.02:   # 약한 상승
    score += 10
elif obv_strength < -0.1:   # 강한 하락
    score -= 15
elif obv_strength < -0.02:  # 약한 하락
    score -= 5
```

#### 1.2 VWAP 점수 대칭화
```python
# 현재
if vwap_pos > 0.6:
    score += 15
elif vwap_pos < 0.4:
    score -= 10

# 개선
if vwap_pos > 0.8:
    score += 20
elif vwap_pos > 0.6:
    score += 15
elif vwap_pos > 0.4:
    score += 5
elif vwap_pos > 0.2:
    score -= 5
elif vwap_pos <= 0.2:
    score -= 20  # 대칭화
```

#### 1.3 Institutional Flow 임계값 조정
```python
# 현재
if inst_flow > 0.3:
    score += 15
elif inst_flow > 0.1:
    score += 5
elif inst_flow < -0.3:
    score -= 15

# 개선
if inst_flow > 0.3:
    score += 15  # 강한 매수
elif inst_flow > 0.15:
    score += 10  # NEW: 중간 매수
elif inst_flow > 0.05:
    score += 5   # 약한 매수
elif inst_flow < -0.3:
    score -= 15  # 강한 매도
elif inst_flow < -0.15:
    score -= 10  # NEW: 중간 매도
elif inst_flow < -0.05:
    score -= 5   # 약한 매도
```

#### 1.4 거래량 감소 페널티
```python
# NEW: 거래량 부족 신호
if volume_trend < 0.8:
    score -= 5   # 20% 이상 낮음
elif volume_trend < 1.0:
    score -= 2   # 약간 낮음
```

---

### Phase 2: 단기 (MFI + AD 추가)

#### 2.1 MFI 점수 추가
```python
# NEW: Money Flow Index 점수
if 'MFI' not in df.columns:
    df = VolumeFlowIndicators.calculate_money_flow_index(df)

mfi = df['MFI'].iloc[-1]

if pd.notna(mfi):
    if mfi > 80:
        score += 10   # 과매수 (반전 신호)
    elif mfi > 60:
        score += 5    # 강한 매수
    elif mfi < 20:
        score -= 10   # 과매도 (반전 신호)
    elif mfi < 40:
        score -= 5    # 약한 매도
```

#### 2.2 AD_Line 점수 추가
```python
# NEW: Accumulation/Distribution Line 점수
if 'AD_Line' not in df.columns:
    df = VolumeFlowIndicators.calculate_accumulation_distribution(df)

# AD_Line 추세 (최근 vs 이전)
if len(df) > 10:
    ad_recent = df['AD_Line'].iloc[-5:].mean()
    ad_older = df['AD_Line'].iloc[-15:-5].mean()
    
    if ad_recent > ad_older:
        score += 5    # 자금 유입
    else:
        score -= 5    # 자금 유출
```

---

### Phase 3: 선택 (Volume Profile + Advanced)

#### 3.1 Volume Profile 점수
```python
# NEW: Volume Profile 활용
profile = analyzer.calculate_volume_profile(df)
peak_levels = profile.get('peak_levels', [])
current_price = profile.get('current_price', 0)

# 가격이 매물대(peak_level) 근처인지 확인
for peak in peak_levels:
    if abs(current_price - peak) / current_price < 0.02:  # 2% 이내
        score -= 3   # 저항 근처 (약간의 페널티)
        break
```

---

## 📈 요구사항 준수 현황

| 요구사항 | 현재 | 개선 필요 |
|---------|------|---------|
| OBV 계산 | ✅ | ⚠️ 점수 강화 필요 |
| VWAP | ✅ | ⚠️ 대칭화 |
| Volume Spike | ✅ | ✅ (양호) |
| Volume Profile | ⚠️ 계산만 | ❌ 점수 미반영 |
| 거래량 추세 | ✅ | ⚠️ 감소 신호 추가 |
| MFI | ❌ 미사용 | ❌ 신규 필요 |
| AD_Line | ❌ 미사용 | ❌ 신규 필요 |

---

## 🔄 개선 효과

### 현재 vs 개선 후

| 시나리오 | 현재 | 개선 | 차이 | 해석 |
|---------|------|------|------|------|
| 강한 수급 | 90 | 90 | - | 동일 (더 다층적) |
| 약한 수급 | 50 | 40 | -10 | 명확한 약세 |
| 기관 매도 | 35 | 25 | -10 | 더 강한 경고 |
| 거래량 부족 | 50 | 45 | -5 | 신호 추가 |
| MFI 과매수 | 50 | 60 | +10 | 반전 신호 |

---

## 💡 거래량 & 수급의 역할

### 정량 점수 분배
```
기술지표:
  이동평균: 30점
  모멘텀: 20점
  변동성: 20점
  거래량/수급: 20점  ← 중요도 높음 (1/5)
  피보나치: 10점

거래량/수급 내부:
  OBV: 4점 (거래량 추세)
  VWAP: 6점 (수급 위치)
  Volume Spike: 2점 (기관 활동)
  MFI: 4점 (거래액 모멘텀)
  AD_Line: 2점 (자금 흐름)
  Institutional: 2점 (기관 수급)
```

### 거래량 부진의 의미
```
상승하는데 거래량 없음:
  = 약한 상승 (확신 부족)
  = 반전 가능성 높음

하락하는데 거래량 많음:
  = 강한 하락 (기관 매도)
  = 더 내려갈 수 있음

거래량 많은데 가격 정체:
  = 기관 수급 중 (대기)
  = 방향성 결정 임박
```

---

## 🚀 권장 개선 순서

### 1순위: 즉시 (Phase 1)
- [ ] OBV 강도 측정
- [ ] VWAP 대칭화
- [ ] Institutional flow 임계값 조정
- [ ] 거래량 감소 페널티

### 2순위: 단기 (Phase 2)
- [ ] MFI 점수 추가
- [ ] AD_Line 점수 추가

### 3순위: 선택 (Phase 3)
- [ ] Volume Profile 활용

