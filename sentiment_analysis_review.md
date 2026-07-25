# 뉴스 감성 분석 로직 검토 보고서

**검토일**: 2026-07-25  
**상태**: 🔍 분석 완료 - 개선 권장

---

## 📋 개요

requirements.md의 요구사항 대비 뉴스 감성(News Sentiment) 분석 로직의 구조적 불일치를 확인했습니다.

### 요구사항 (requirements.md)
```
정성 점수 (뉴스 감성): 총 100점
  - 거시경제 뉴스 감성: 30점
  - 개별 종목 뉴스 감성: 40점
  - 전문가 평가: 30점
  
최종 점수 = 정량 60% + 정성 40% = 최종 랭킹
```

### 현재 구현 상태
```
✅ TextBlob/Claude 감성 분석: 구현됨
✅ 전문가 의견 (expert opinion): 구현됨
❌ 거시 vs 종목 뉴스 분리: 미구현
❌ 3개 요소 통합 (30+40+30): 미구현
❌ 정성 점수 최종 반환: 단순 단일 점수만
```

---

## ❌ 발견된 문제점

### 1. **거시 vs 종목 뉴스 분리 로직 완전 부재**

**요구사항**: "거시경제 뉴스 감성 30점" vs "개별 종목 뉴스 감성 40점"

**현재 구현**:
```python
def analyze_articles_sentiment(
    self,
    articles: List[Dict],
    use_titles_only: bool = False
) -> Dict:
    """
    여러 기사의 감성을 분석
    
    단순히 기사 리스트를 받음 → 구분 로직 없음
    """
    for article in articles:
        # 모든 기사를 동일하게 처리
        text = f"{article.get('title', '')} {article.get('description', '')}"
        polarity, label = self.analyze_sentiment_textblob(text)
```

**문제점**:
```
1. 뉴스 소스 구분 없음
   → "거시경제" vs "종목" 판단 불가능
   → 예: Federal Reserve 뉴스 vs Apple 실적 뉴스

2. 30:40 가중치 적용 불가능
   → 모든 기사가 동일 비중
   
3. 뉴스 수집 단계에서도 분리 필요
   → collectors/news_data.py의 search_macro_news()
   → collectors/news_data.py의 search_ticker_news()
   → 이미 분리되어 있지만 점수에 미반영
```

---

### 2. **전문가 의견 통합 미흡**

**현재 상태**:
```python
def analyze_expert_opinion(
    self,
    ticker: str,
    articles: List[Dict]
) -> Dict:
    """
    Claude를 통한 전문가 의견 분석
    0-100 점수 반환 (0=약세, 50=중립, 100=강세)
    """
    # BUT: 감성 점수(정성 점수)에 통합되지 않음
    # 단순히 별도 데이터로만 반환
```

**문제점**:
```
1. 별도 계산되지만 최종 감성 점수에 미반영
2. 3개 요소(거시 30 + 종목 40 + 전문가 30)가 합쳐지지 않음
3. ranker.py의 sentiment_score가 단순 하나의 숫자일 뿐
   → 30/40/30 구조 손실
```

---

### 3. **정성 점수 통합 로직 부재**

**요구사항**:
```
정성 점수 = (거시 감성 × 30) + (종목 감성 × 40) + (전문가 × 30)
          ÷ 100 (정규화)
```

**현재 구현**:
```python
# sentiment_score.py
def analyze_ticker_sentiment(
    ticker: str,
    articles: List[Dict],
    use_claude: bool = False
) -> Dict:
    # 단순히 기사 감성만 반환
    basic_sentiment = analyzer.analyze_articles_sentiment(articles)
    basic_score = analyzer.convert_to_score(basic_sentiment)
    
    # 전문가 의견은 별도
    if use_claude:
        claude_result = claude_analyzer.analyze_expert_opinion(articles, ticker)
        # → result에 추가되지만 통합 공식 없음

# ranker.py
# sentiment_score는 단순히 0-100 점수
# 3개 요소 구분 정보 없음
```

**문제점**:
```
1. calculate_qualitative_score() 함수 부재
2. 3개 요소를 0-100으로 정규화해서 30/40/30으로 합쳐야 하는데
   → 현재는 단일 점수만 반환
3. 거시/종목 분리된 감성 정보도 없음
```

---

### 4. **뉴스 수집의 거시/종목 분리가 점수에 미반영**

**현재 상태** (src/collectors/news_data.py):
```python
def search_macro_news():
    # 거시경제 뉴스 수집 (Federal Reserve, GDP, Inflation 등)
    pass

def search_ticker_news():
    # 종목별 뉴스 수집 (실적, 제품 발표 등)
    pass

# 이미 분리되어 수집됨!
# BUT: sentiment 점수에 통합되지 않음
```

**문제점**:
```
수집 단계에서는 분리되지만
→ 감성 분석 단계에서 재통합되면서 구분 정보 손실
→ 점수 반영 단계에서는 최종적으로 하나의 점수만 있음
```

---

### 5. **LLM 모델 선택 불명확**

**현재 상태**:
```python
# analyze_with_claude()
response = self.client.messages.create(
    model="claude-opus-4-1",  # 하드코딩됨
    max_tokens=500,
    messages=[...])

# analyze_expert_opinion()
response = self.client.messages.create(
    model=self.model,  # config.settings의 CLAUDE_MODEL
    max_tokens=300,    # 다른 값
    messages=[...])

# → 모델 선택, max_tokens가 일관성 없음
```

**문제점**:
```
1. 모델과 파라미터가 함수마다 다름
2. API 비용/성능 트레이드오프 불명확
3. fallback 메커니즘 없음 (API 실패 시 50.0 반환)
```

---

### 6. **TextBlob vs Claude 선택 정책 없음**

**현재 상태**:
```python
# SentimentAnalyzer: TextBlob 사용
# AICLaudeSentimentAnalyzer: Claude 사용

# 사용 정책이 불명확
def analyze_ticker_sentiment(
    ticker: str,
    articles: List[Dict],
    use_claude: bool = False  # 기본값 False (TextBlob)
) -> Dict:
    pass
```

**문제점**:
```
1. TextBlob는 속도 우선, 정확도 낮음
2. Claude는 정확하지만 비용/지연 높음
3. 하이브리드 접근 없음 (e.g., 텍스트 길이에 따라 선택)
4. 요구사항에서는 "방법 1: VADER, 방법 2: LLM"이라고만 함
   → 어느 것을 기본 사용할지 불명확
```

---

## 📊 점수 분포 비교 (현재 vs 개선 안)

### 종목 호재 + 긍정적 거시
```
현재:
  모든 뉴스 합쳐서 단일 감성 분석
  결과: 65점 (구성 모름)

개선 후:
  거시 뉴스: 75점 → 75 × 0.30 = 22.5
  종목 뉴스: 70점 → 70 × 0.40 = 28.0
  전문가: 80점 → 80 × 0.30 = 24.0
  합계: 74.5점 (명확한 구성)
```

### 종목 약재 + 중립적 거시
```
현재:
  감성: 45점 (구성 모름)

개선 후:
  거시: 50점 → 50 × 0.30 = 15.0
  종목: 40점 → 40 × 0.40 = 16.0
  전문가: 50점 → 50 × 0.30 = 15.0
  합계: 46.0점 (명확한 약세)
```

---

## ✨ 개선안

### Phase 1: 즉시 적용 (필수)

#### 1.1 거시 vs 종목 뉴스 감성 분리
```python
def calculate_qualitative_score(
    ticker: str,
    macro_articles: List[Dict],
    ticker_articles: List[Dict],
    use_claude: bool = False
) -> Tuple[float, Dict]:
    """
    거시/종목/전문가 3개 요소를 통합한 정성 점수 계산
    
    Args:
        macro_articles: 거시경제 뉴스 (무관심하게 받음)
        ticker_articles: 종목 뉴스
        use_claude: Claude 사용 여부
    
    Returns:
        (정성_점수, 상세_정보)
        정성_점수 = (macro_score × 30 + ticker_score × 40 + expert_score × 30) / 100
    """
    analyzer = SentimentAnalyzer()
    
    # 거시 감성
    macro_sentiment = analyzer.analyze_articles_sentiment(macro_articles)
    macro_score = analyzer.convert_to_score(macro_sentiment)  # 0-100
    
    # 종목 감성
    ticker_sentiment = analyzer.analyze_articles_sentiment(ticker_articles)
    ticker_score = analyzer.convert_to_score(ticker_sentiment)  # 0-100
    
    # 전문가 의견
    expert_analyzer = AICLaudeSentimentAnalyzer()
    expert_result = expert_analyzer.analyze_expert_opinion(
        ticker, 
        ticker_articles  # 종목 뉴스 기반
    )
    expert_score = expert_result['score']  # 0-100
    
    # 통합
    qualitative_score = (
        (macro_score × 0.30) +
        (ticker_score × 0.40) +
        (expert_score × 0.30)
    )
    
    detail = {
        'macro_score': round(macro_score, 1),
        'ticker_score': round(ticker_score, 1),
        'expert_score': round(expert_score, 1),
        'expert_analysis': expert_result['analysis'],
        'expert_parsed': expert_result['parsed']
    }
    
    return round(qualitative_score, 1), detail
```

#### 1.2 Sentiment 점수 구조 확장
```python
# ranker.py의 StockScore 데이터클래스 확장

@dataclass
class StockScore:
    ticker: str
    technical_score: float
    sentiment_score: float  # 최종 정성 점수 (0-100)
    
    # NEW: 정성 점수 상세
    sentiment_macro_score: float = 0.0      # 거시 감성
    sentiment_ticker_score: float = 0.0     # 종목 감성
    sentiment_expert_score: float = 0.0     # 전문가
    sentiment_detail: Dict = None           # 분석 텍스트 등
    
    overall_score: float = 0.0
    ...
```

---

### Phase 2: 단기 (선택사항)

#### 2.1 하이브리드 모델 선택
```python
def analyze_articles_sentiment(
    articles: List[Dict],
    use_claude: bool = None  # None = auto select
) -> Dict:
    """
    TextBlob vs Claude 자동 선택
    """
    if use_claude is None:
        # 자동 선택: 기사 수가 많으면 TextBlob, 적으면 Claude
        if len(articles) > 5:
            use_claude = False  # 속도 우선
        else:
            use_claude = True   # 정확도 우선
    
    if use_claude:
        return analyze_with_claude(articles)
    else:
        return analyze_with_textblob(articles)
```

#### 2.2 모델 파라미터 통일
```python
# config/settings.py에 추가
CLAUDE_MODEL = "claude-opus-5"  # 최신 모델
SENTIMENT_MAX_TOKENS = 300  # 모든 sentiment 분석에 통일
EXPERT_OPINION_MAX_TOKENS = 300
```

---

## 📈 요구사항 준수 현황

| 요구사항 | 현재 | 개선 필요 |
|---------|------|---------|
| 거시 감성 (30점) | ❌ 미분리 | ✅ 분리 필요 |
| 종목 감성 (40점) | ❌ 미분리 | ✅ 분리 필요 |
| 전문가 평가 (30점) | ⚠️ 존재 | ✅ 통합 필요 |
| 정성 점수 통합 | ❌ 없음 | ✅ 신규 필요 |
| Claude API | ✅ 구현 | ⚠️ 통일 필요 |
| TextBlob 호환 | ✅ 구현 | ✅ 양호 |

---

## 🔄 개선 효과

### 개선 전
```
sentiment_score = 65.0  # 어떻게 계산됐는지 불명확
전체 점수 = tech × 0.6 + 65 × 0.4 = ???
```

### 개선 후
```
거시 감성: 70점
종목 감성: 75점
전문가: 80점

정성 점수 = (70 × 0.30) + (75 × 0.40) + (80 × 0.30)
         = 21.0 + 30.0 + 24.0
         = 75.0점

전체 점수 = tech × 0.6 + 75 × 0.4
          = 더 명확한 최종 점수

리포트:
  "거시경제는 호황(70), 종목은 강세(75), 전문가 강기(80)"
```

---

## 💡 정성 점수의 역할

### 최종 점수 공식 (requirements)
```
최종 점수 = 정량(기술) × 0.6 + 정성(감성) × 0.4

정량: 100점 (이동평균30 + 모멘텀20 + 변동성20 + 거래량20 + 피보나치10)
정성: 100점 (거시30 + 종목40 + 전문가30)

예: 정량 80점, 정성 70점
→ 최종 = 80 × 0.6 + 70 × 0.4 = 48 + 28 = 76점
```

### 거시 vs 종목 감성의 의미
```
거시 감성 (30점):
  - Fed 금리/인플레이션/경기지표
  - 전체 시장 리스크 온/오프
  - 예: Fed 긴축 → 모든 주식에 악영향

종목 감성 (40점, 비중 높음):
  - 실적, 제품 발표, CEO 발언
  - 개별 기업의 경쟁력
  - 예: Apple 신제품 성공 → Apple 주가 상승

전문가 (30점):
  - 위 두 가지를 종합한 1주일 방향성
  - "기술은 좋지만 거시가 악악하니 -5% 가능"
  - 맥락 기반 최종 판단
```

---

## 🚀 권장 개선 순서

### 1순위: 즉시 (Phase 1)
- [ ] calculate_qualitative_score() 함수 신규 추가
- [ ] 거시/종목 뉴스 분리 감성 분석
- [ ] 전문가 의견 통합 (30% 가중치)
- [ ] StockScore 확장 (sentiment 상세)
- [ ] ranker.py 통합

### 2순위: 선택 (Phase 2)
- [ ] 하이브리드 모델 선택 (TextBlob vs Claude)
- [ ] 모델 파라미터 통일

