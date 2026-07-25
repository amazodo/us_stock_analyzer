# CLAUDE.md — 프로젝트 가이드

이 파일은 Claude Code가 이 프로젝트에서 작업할 때 자동으로 읽는 지침 파일이다.
프로젝트 루트에 `CLAUDE.md`라는 이름으로 두면 세션 시작 시 자동으로 컨텍스트에 로드된다.

---
### 로컬 환경 정보

- OS: Windows
- 작업 디렉토리: 프로젝트 루트 기준으로 실행할 것

---

## 2. 필수 세팅

### 설정 파일 위치

| 파일 | 용도 |
|------|------|
| `<프로젝트>/CLAUDE.md` | 프로젝트별 지침 (이 파일) |
| `~/.claude/settings.json` | 전역 설정 (권한, 훅, 환경변수) |
| `<프로젝트>/.claude/settings.json` | 프로젝트 설정 (팀 공유, git 커밋) |
| `<프로젝트>/.claude/settings.local.json` | 개인 설정 (git 제외) |

### 배포 규칙 (중요)

- **배포는 `git push origin main`으로만 한다.**
- Netlify CLI, Vercel CLI 등으로 직접 배포하지 마.
- 배포·서버 구성은 기존 방식 그대로 유지하고 임의로 바꾸지 마.

---

## 3. 하네스(Harness) 기본 내용

하네스란 Claude가 실제로 동작하는 실행 환경(도구, 권한, 컨텍스트 관리)을 말한다.

대화가 길어지면 자동으로 요약(compact)되어 다음 컨텍스트로 이어진다.

---

## 4. 작업 원칙 (요약)

우선순위: **정확성 > 검증 > 최소 변경 > 명확성 > 유지보수성**

- 파일·API·스키마가 존재한다고 가정하지 말고 먼저 읽어서 확인해.
- 수정 전에 관련 파일을 읽고, 수정 후에는 테스트·실행으로 검증해.
- 요청된 작업에만 변경을 국한하고, 관련 없는 리팩토링은 하지 마.
- 가장 단순한 해결책을 선호하고, 불필요한 의존성·추상화를 추가하지 마.
- 기존 프로젝트의 관례와 스타일을 따라.
- 막히면 멈추고 무엇이 막혔는지, 무엇이 검증됐는지 명확히 보고해.
- 검증 없이 "성공했다"고 주장하지 마.

---

## 5. 프로젝트별 정보 (직접 채워 넣기)

> 아래 항목은 프로젝트마다 수정해서 사용.

# CLAUDE.md - AI Developer Guide

## Core Commands
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Full Pipeline**: `python main.py --top 5`
- **Run Technical Analysis Only**: `python main.py --mode technical`
- **Run News Analysis Only**: `python main.py --mode news`
- **Run Tests**: `pytest tests/`

## Technology Stack
- **Language**: Python 3.10+
- **Market Data**: `yfinance`, `pandas`, `numpy`
- **Technical Analysis**: `ta` or `pandas_ta`
- **News / Web Search**: `newsapi-python` or DuckDuckGo / Tavily Search API
- **AI / LLM Logic**: `anthropic` or `openai` API for Sentiment & Summarization

## Architecture Rules
1. **Modular Design**: 데이터 수집(`collectors`), 지표 계산(`indicators`), 평가 및 추천(`analysis`, `recommender`)을 명확히 분리한다.
2. **Error Handling**: 특정 종목 데이터 수집 실패 시 전체 프로세스가 멈추지 않고 스킵되도록 에러 로깅 처리.
3. **Reproducibility**: 지표 계산 공식은 표준 라이브러리(`ta`) 기준과 정확히 일치시킨다.
4. **No Hardcoding**: API 키는 `.env`로 관리하고, 가중치와 지표 파라미터는 `config/settings.py`에서 관리한다.


