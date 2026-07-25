# 🚀 START HERE - 초보자를 위한 완벽 가이드

**Streamlit을 처음 사용하시나요?** 걱정 마세요! 이 가이드를 따라하면 **20분 안에 웹앱을 실행**할 수 있습니다. 👍

---

## 📱 **가장 빠른 방법: 폰에서 바로 사용하기** (2분)

### 1️⃣ **아무 설정 없이 바로 사용**
브라우저에서 다음 주소를 입력하세요:
```
https://amazodo-us-stock-analyzer.streamlit.app
```

✅ 끝! 이제 분석이 시작됩니다.

---

## 💻 **로컬 컴퓨터에서 실행하기** (10분)

Streamlit이 무엇인지 모르셔도 괜찮습니다. 단계별 따라하세요.

### **Step 1: Python 설치 확인** (2분)

Windows에서 **Command Prompt** 또는 **PowerShell** 열기:

```bash
python --version
```

✅ `Python 3.10.0` 이상이 나오면 다음으로!
❌ 명령어를 찾을 수 없다면: https://www.python.org 에서 설치

### **Step 2: 코드 다운로드** (1분)

**옵션 A: ZIP 파일로 다운로드** (가장 쉬움)
1. GitHub: https://github.com/amazodo/us_stock_analyzer
2. 초록색 **<> Code** 버튼 클릭
3. **Download ZIP** 클릭
4. 압축 해제 (원하는 폴더)

**옵션 B: Git 사용** (개발자용)
```bash
git clone https://github.com/amazodo/us_stock_analyzer.git
cd us_stock_analyzer
```

### **Step 3: 필수 패키지 설치** (5분)

**Command Prompt에서:**

```bash
# 1단계: 폴더 이동
cd C:\Users\YourName\Downloads\us_stock_analyzer

# 2단계: 가상환경 생성 (권장)
python -m venv venv

# 3단계: 가상환경 활성화
venv\Scripts\activate

# 4단계: 패키지 설치 (인터넷 필요, 시간 걸림)
pip install -r requirements.txt
```

> 💡 **가상환경이란?** 이 프로젝트만의 독립된 Python 환경입니다. 다른 프로젝트와 충돌하지 않습니다.

### **Step 4: API 키 설정** (2분)

#### NewsAPI 키 얻기:
1. https://newsapi.org 접속
2. **Get API Key** 클릭
3. 이메일로 가입
4. API Key 복사 (예: `abc123xyz789`)

#### .env 파일 만들기:
**같은 폴더에서** `.env` 라는 파일을 생성하세요:

```env
NEWS_API_KEY=abc123xyz789
```

> ⚠️ **중요**: `.env` 파일은 절대 GitHub에 올리지 마세요! (이미 `.gitignore`에 설정됨)

### **Step 5: Streamlit 앱 실행** (1분)

같은 Command Prompt에서:

```bash
streamlit run app.py
```

그럼 자동으로 브라우저가 열립니다! 🎉

```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

---

## 🌐 **온라인에서 실행하기** (모바일에서도!) (15분)

### **장점:**
- ✅ 어디서든 접속 가능 (폰, 태블릿, PC)
- ✅ 자동으로 최신 코드 반영
- ✅ 친구들과 URL 공유 가능
- ✅ 24/7 실행 중

### **필요한 것:**
- ✅ GitHub 계정 (무료)
- ✅ Streamlit 계정 (무료)
- ✅ 5분의 시간

### **배포 단계:**

#### **1단계: GitHub에 로그인**
1. https://github.com/amazodo/us_stock_analyzer 접속
2. **Sign in** (이미 로그인된 계정)
3. 코드가 보이면 성공! ✅

#### **2단계: Streamlit Cloud 배포**

1. **https://streamlit.io** 접속
2. **Sign in** → **GitHub로 로그인**
3. 우측 상단에서 **Create app** 클릭
4. 다음 정보 입력:
   - **Repository**: `amazodo/us_stock_analyzer`
   - **Branch**: `main`
   - **Main file path**: `app.py`

5. **Deploy** 클릭 → ⏳ 1-2분 기다리기

#### **3단계: API 키 설정**

배포 완료 후:

1. 앱 화면 우측 상단 **☰ (세로 세 줄)** 클릭
2. **Settings** 선택
3. **Secrets** 탭 클릭
4. 다음 입력:
   ```toml
   NEWS_API_KEY = "your-api-key-here"
   ```
   (API 키 부분을 실제 키로 바꾸세요)
5. **Save** 클릭

✅ 앱이 자동으로 재시작됩니다!

#### **4단계: 배포 완료!**

앱 URL:
```
https://amazodo-us-stock-analyzer.streamlit.app
```

이제 어디서든 이 URL을 열면 됩니다! 📱

---

## 🎯 **앱 사용 방법**

### **화면 구성**

```
┌─────────────────────────────────────┐
│  좌측 사이드바                       │
│  ⚙️ 분석 설정                        │
│  - 분석 기간 선택                   │
│  - 🚀 분석 시작 버튼                │
│                                     │
│                                     │
│  메인 화면                          │
│  📊 Top 5 추천 종목                  │
│  📈 상세 분석                       │
│  📰 뉴스                            │
│  📥 리포트 다운로드                  │
└─────────────────────────────────────┘
```

### **사용 순서**

#### **1단계: 분석 기간 선택**
좌측 사이드바에서:
- **1개월** (빠르고 최신 정보)
- **3개월** (중기 추세)
- **6개월** (중장기)
- **1년** (장기 추세, 시간 오래 걸림)

#### **2단계: 분석 시작**
**🚀 분석 시작** 버튼 클릭

⏳ 기다리기:
- 첫 로드: 3-10분 (처음엔 오래 걸림)
- 두 번째: 더 빠름 (캐시 사용)

#### **3단계: 결과 확인**

**📊 Top 5 추천 종목** 섹션에서:
- **종목 코드** (예: AAPL, MSFT)
- **종합 점수** (0-100, 높을수록 좋음)
- **기술 점수** (6개 지표 종합)
- **최신 뉴스** (클릭 가능한 링크)

#### **4단계: 상세 분석 보기**

**📈 종목별 상세 분석** 탭:
- 종목 선택
- **📊 차트**: 기술적 차트 (Ichimoku, Moving Average 등)
- **📈 점수분석**: 각 지표별 세부 점수
- **📰 뉴스**: 최신 뉴스 기사

#### **5단계: 리포트 다운로드**

**📥 보고서 내보내기** 버튼:
- 📄 **마크다운** (메모장에서 열기 가능)
- 📊 **JSON** (엑셀에서 열기 가능)

---

## 📊 **6개 기술 지표 설명**

### **이동평균 (24%)**
- 최근 가격 추세가 상승하는가?
- 예: SMA(20), EMA(12) 등

### **모멘텀 (16%)**
- 매수/매도 강도는?
- 예: RSI (과매도 상태), MACD (추세 확인)

### **변동성 (16%)**
- 가격이 얼마나 변하는가?
- 예: Bollinger Bands, ATR

### **거래량/수급 (16%)**
- 큰 자금이 들어오는가?
- 예: OBV (거래량), VWAP (거래량 가중 평균)

### **피보나치 (8%)**
- 지지/저항선은 어디인가?
- 예: 61.8%, 38.2% 반전선

### **일목균형표 (20%)**
- 구름대 위에 있는가? (강세)
- 전환선 > 기준선? (상승신호)

---

## ⚙️ **자주 묻는 질문 (FAQ)**

### **Q1: 분석이 너무 느려요**
**A:** 
- 첫 실행은 느림 (캐시 빌드 중) → 2-3분 기다리세요
- 분석 기간을 줄여보세요 (1년 → 3개월)
- Streamlit Cloud는 무료이므로 가끔 느릴 수 있습니다

### **Q2: "뉴스가 표시 안 되요"**
**A:**
- NewsAPI 할당량 초과 (무료: 100건/일)
- 다음 날(UTC 자정)에 다시 시도하세요
- API 키가 설정되었는지 확인하세요 (Settings → Secrets)

### **Q3: 로컬에서 "pip install" 에러**
**A:**
```bash
# 이것을 실행해보세요:
pip install --upgrade pip
pip install -r requirements.txt
```

### **Q4: 로컬에서 "streamlit: 명령어를 찾을 수 없음"**
**A:**
```bash
# 가상환경이 활성화되어 있는지 확인:
venv\Scripts\activate  # 다시 활성화

# 그 다음 실행:
python -m streamlit run app.py
```

### **Q5: 배포 후 "API Key not found"**
**A:**
1. Streamlit Cloud 앱 → Settings → Secrets 확인
2. `NEWS_API_KEY = "..."` 입력했는지 확인
3. Save 버튼을 눌렀는지 확인
4. 3분 후 새로고침

### **Q6: 코드를 수정했는데 반영 안 됨**
**A:**
로컬에서:
```bash
git add .
git commit -m "Update"
git push origin main
```
→ Streamlit Cloud가 1-2분 내 자동 반영

### **Q7: 폰에서도 실행 가능한가?**
**A:** ✅ 완벽히 가능합니다!
- Safari (iPhone/iPad)
- Chrome (Android)
- 모든 브라우저 지원

---

## 🔍 **분석 결과 해석하기**

### **점수 범위**
- **80-100점**: 매우 강한 상승신호 🟢
- **60-79점**: 긍정적 신호 🟡
- **40-59점**: 중립 ⚪
- **20-39점**: 부정적 신호 🔴
- **0-19점**: 매우 약한 신호 ⚫

### **실제 사례**
```
#1. AAPL | 점수 75/100 | 뉴스 3개
→ 해석: 강한 상승신호 + 관심도 높음 (뉴스 많음)
→ 행동: 관심 종목 리스트에 추가

#2. MSFT | 점수 45/100 | 뉴스 0개  
→ 해석: 신호 약함 + 관심도 낮음
→ 행동: 지켜보기 (아직 때가 아님)
```

---

## ⚠️ **중요 주의사항**

### **이것은 투자 조언이 아닙니다!**
- 본 시스템은 **정보 제공 목적**입니다
- 과거 성과는 미래를 보장하지 않습니다
- **항상 본인의 판단**으로 투자하세요
- 필요시 **금융 전문가** 상담받으세요

### **리스크 관리**
```
추천: 자산의 1-5%만 투자
     (예: 1000만원 → 50-500만원)
     
피해야 할 것:
     ❌ 전 자산 투자
     ❌ 빌려서 투자 (마진)
     ❌ 한 종목에만 집중
```

---

## 📞 **도움말**

### **문제 해결**
- **GitHub Issues**: https://github.com/amazodo/us_stock_analyzer/issues
- **Streamlit Docs**: https://docs.streamlit.io

### **더 배우기**
- 기술적 지표 원리: TradingView(www.tradingview.com)
- 주식 투자 기초: 유튜브 "주식 기초" 검색

### **개선 제안**
GitHub에서 **Issues** 탭 → **New Issue**로 의견 전달

---

## 🎉 **축하합니다!**

이제 당신은:
- ✅ Streamlit 웹앱 사용 가능
- ✅ 폰/PC 어디서든 접속 가능
- ✅ 실시간 주식 분석 가능
- ✅ 뉴스 통합 분석 가능

**Happy Trading! 📈**

---

**마지막 팁:** 북마크를 해두세요!
```
https://amazodo-us-stock-analyzer.streamlit.app
```

