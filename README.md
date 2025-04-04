# GovDraft - 정부 문서 템플릿 검색 시스템

공공데이터포털 API를 활용하여 다양한 정부 문서 템플릿(보도자료, 연설문, 정책 보고서, 발간사, 회의·행사 계획 등)을 검색하고 선택할 수 있는 웹 애플리케이션입니다.

## 기능

- 키워드 검색: 원하는 키워드로 템플릿 검색
- 필터링: 문서 유형, 발행 부처 등으로 필터링
- 상세 정보 확인: 각 템플릿의 상세 정보 확인
- 템플릿 선택: 원하는 템플릿 선택 및 사용

## 기술 스택

- Python 3.13.2
- Flask 3.0.3
- Tailwind CSS (CDN 방식)
- 공공데이터포털 API

## 설치 및 실행 방법

### 1. 필요 조건

- Python 3.13.2
- pip (패키지 관리자)

### 2. 저장소 복제

```bash
git clone https://github.com/yourusername/govdraft.git
cd govdraft
```

### 3. 가상 환경 설정 (선택사항)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 4. 의존성 설치

Python 3.13.2 환경에서는 tiktoken 패키지 설치를 위해 특별한 옵션이 필요합니다:

```bash
# 환경 변수 설정
# Windows
set PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
# Linux/Mac
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# requirements.txt의 다른 패키지 설치
pip install -r requirements.txt

# tiktoken만 별도 설치 (이미 requirements.txt에 포함되어 있지만, 직접 설치 시)
pip install tiktoken --no-build-isolation
```

### 5. 환경 변수 설정

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가합니다:

```
LOG_LEVEL=INFO
PUBLIC_DATA_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
```

공공데이터포털 API 키는 [공공데이터포털](https://www.data.go.kr/)에서 발급받을 수 있습니다.

### 6. 애플리케이션 실행

```bash
python app.py
```

웹 브라우저에서 `http://localhost:5000`으로 접속하여 애플리케이션을 사용할 수 있습니다.

## 웹 애플리케이션 사용법

1. 메인 화면에서 검색창에 원하는 키워드 입력
2. 필터 옵션을 사용하여 결과 정제
3. 검색 결과에서 원하는 템플릿의 '상세 보기' 클릭
4. 상세 정보 확인 후 '이 템플릿 선택' 버튼 클릭

## 명령줄 도구 사용법

템플릿 검색을 위한 명령줄 도구도 제공합니다:

```bash
python main.py
```

프롬프트에 따라 검색 키워드를 입력하면 결과가 `templates.json` 파일로 저장됩니다.

## 로깅

애플리케이션 로그는 `logs` 디렉토리에 `govdraft_YYYYMMDD.log` 형식으로 저장됩니다.

## 문제 해결

### tiktoken 설치 오류

Python 3.13.2에서 tiktoken 설치 시 다음과 같은 오류가 발생할 수 있습니다:

```
error: cargo failed with code: 1 
```

이 문제를 해결하려면:

1. `.env` 파일에 `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` 환경 변수 추가
2. 명령줄에서 `pip install tiktoken --no-build-isolation` 명령 실행

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요. 