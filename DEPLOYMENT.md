# 🚀 Streamlit Cloud 배포 가이드

모바일에서도 접속 가능한 웹앱을 3단계로 배포하세요!

---

## 📋 사전 준비

- ✅ GitHub 계정 (github.com)
- ✅ Streamlit Cloud 계정 (streamlit.io)
- ✅ NewsAPI 키 (newsapi.org)

---

## 🔑 Step 1: API 키 준비

### NewsAPI 가입
1. https://newsapi.org 접속
2. "Get API Key" 클릭
3. 이메일로 가입
4. API Key 복사

```
예: abc123def456ghi789jkl012
```

---

## 📤 Step 2: GitHub에 코드 업로드

### 2.1 저장소 생성
1. GitHub에서 **New Repository** 클릭
2. Repository name: `us-stock-analyzer`
3. **Public** 선택 (중요!)
4. **Create repository**

### 2.2 코드 푸시
```bash
cd d:/claude_code/us_stock_analyzer

# Git 초기화
git init
git add .
git commit -m "Initial commit: US Stock AI Analyzer v2.0"

# 원격 저장소 추가
git remote add origin https://github.com/YOUR-USERNAME/us-stock-analyzer.git

# 메인 브랜치로 푸시
git branch -M main
git push -u origin main
```

✅ 확인: GitHub에서 코드가 보이는지 확인하세요

---

## 🚀 Step 3: Streamlit Cloud 배포

### 3.1 Streamlit Cloud 로그인
1. https://streamlit.io 접속
2. **Sign in** → GitHub로 로그인

### 3.2 앱 배포
1. **Create app** 클릭
2. 다음 정보 입력:
   - **Repository**: `YOUR-USERNAME/us-stock-analyzer`
   - **Branch**: `main`
   - **Main file path**: `app.py`
3. **Deploy** 클릭

⏳ 배포 중... (1-2분)

### 3.3 배포 완료! 🎉
앱 URL: `https://your-username-us-stock-analyzer.streamlit.app`

---

## 🔐 Step 4: API 키 설정 (중요!)

### 방법 1: Streamlit Cloud Secrets (권장)

**Streamlit Cloud 대시보드:**

1. https://share.streamlit.io 접속
2. 배포한 앱 클릭
3. 우측 상단 **☰** → **Settings** 클릭
4. **Secrets** 탭 클릭
5. 다음 내용 복사-붙여넣기:

```toml
NEWS_API_KEY = "your-news-api-key-here"
ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
```

6. **Save** 클릭

✅ 앱이 자동으로 재시작되고 API 키를 사용할 수 있습니다

### 방법 2: 환경 변수 설정 (대안)

**Streamlit Cloud 대시보드:**

1. 앱 설정 → **Edit secrets**
2. 동일한 내용 입력

---

### 🔑 API 키 얻기

**NewsAPI 키** (뉴스 통합용):
1. https://newsapi.org 접속
2. "Get API Key" 클릭
3. 이메일로 가입
4. 대시보드에서 API Key 복사

**Anthropic API 키** (선택사항, 없어도 작동):
1. https://console.anthropic.com 접속
2. API Keys 메뉴 클릭
3. 키 생성 및 복사

---

## 📱 Step 5: 모바일에서 접속

브라우저에서 다음 주소를 입력하세요:

```
https://your-username-us-stock-analyzer.streamlit.app
```

**모든 기기에서 작동합니다:**
- 🖥️ 데스크톱
- 💻 노트북
- 📱 iPhone/iPad (Safari)
- 📱 Android (Chrome)

---

## 🔄 업데이트 방법

코드를 수정한 후:

```bash
git add .
git commit -m "Update: 설명"
git push origin main
```

Streamlit Cloud가 자동으로 감지하고 앱을 업데이트합니다! (1-2분)

---

## 🐛 문제 해결

### Q: 배포 실패
→ Logs 확인: **Settings → Logs**
→ 대부분 의존성 문제이므로 `requirements.txt` 확인

### Q: "API Key not found"
→ Secrets 설정을 다시 확인하세요
→ 키 입력 후 저장했는지 확인

### Q: 뉴스가 표시 안 됨
→ NewsAPI 할당량 초과 (무료: 100/day)
→ 다음 날 다시 시도하세요

### Q: 앱이 느림
→ 첫 로드는 3-5초 소요
→ Streamlit은 서버리스이므로 정상

---

## 📊 모니터링

배포 후 Streamlit Cloud에서:
- 사용 통계 확인
- 로그 모니터링
- 성능 추적

---

## 🎯 다음 단계

1. ✅ 배포 완료
2. ✅ 모바일에서 테스트
3. 📧 친구들과 공유
4. 🐛 피드백 반영
5. 🔄 지속적인 업데이트

---

## 💡 팁

**속도 최적화:**
```python
# app.py 시작에 추가
@st.cache_resource
def init_pipeline():
    return AnalysisPipeline()
```

**커스텀 도메인** (선택사항):
Streamlit Cloud → **Settings → Custom domain**

---

## 📞 지원

- Streamlit Docs: https://docs.streamlit.io
- GitHub Issues: GitHub 리포지토리의 Issues 탭
- Community: https://discuss.streamlit.io

---

**축하합니다! 이제 당신의 웹앱이 온라인입니다! 🚀**

