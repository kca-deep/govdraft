# GovDraft - 정부 문서 템플릿 검색 및 활용 도구

GovDraft는 공공데이터포털 API를 활용하여 정부 문서 템플릿을 검색하고, 이를 기반으로 
보고서를 작성할 수 있도록 도와주는 웹 애플리케이션입니다.

## 주요 기능

- 다양한 정부 문서 템플릿 검색 (보도자료, 연설문, 발간사, 정책보고서, 회의/행사계획)
- 검색 결과 필터링 및 정렬
- 템플릿 상세 내용 확인
- 선택한 템플릿을 기반으로 AI 보고서 생성
- 사용자 계정 관리 (회원가입, 로그인, 프로필 관리)

## 설치 및 실행 방법

### 사전 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)
- 공공데이터포털 API 키 (환경 변수로 설정)

### 설치 단계

1. 저장소를 클론합니다.
   ```bash
   git clone https://github.com/yourusername/govdraft.git
   cd govdraft
   ```

2. 가상 환경을 생성하고 활성화합니다.
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수를 설정합니다. `.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가합니다.
   ```bash
   PUBLIC_DATA_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_for_flask
   ```

5. 데이터베이스를 초기화하고 애플리케이션을 실행합니다.
   ```bash
   python app.py
   ```

6. 웹 브라우저에서 `http://localhost:5000`으로 접속하여 애플리케이션을 사용합니다.

## 프로젝트 구조

```
govdraft/
├── app.py                  # 애플리케이션 진입점
├── config.py               # 환경변수 및 설정 관리
├── requirements.txt        # 의존성 패키지 목록
├── .env                    # 환경 변수 파일 (git에 포함되지 않음)
├── .gitignore              # git 무시 파일 목록
├── api/                    # API 관련 모듈
│   ├── __init__.py
│   └── government_api.py   # 공공데이터포털 API 연동
├── routes/                 # 라우트 핸들러
│   ├── __init__.py
│   ├── main.py             # 메인 페이지 및 검색 관련 라우트
│   ├── drafts.py           # 보고서 생성 관련 라우트
│   └── member/             # 회원 관리 모듈
│       ├── __init__.py
│       ├── forms.py        # 회원 관련 폼 정의
│       ├── models.py       # 사용자 모델 정의
│       └── routes.py       # 회원 관련 라우트
├── utils/                  # 유틸리티 함수
│   ├── __init__.py
│   ├── html_utils.py       # HTML 처리 유틸리티
│   ├── logging.py          # 로깅 설정
│   └── token_utils.py      # 토큰 비용 계산 유틸리티
├── logs/                   # 로그 파일 디렉토리
│   └── .gitkeep
└── web/                    # 웹 템플릿 및 정적 파일
    ├── base.html           # 기본 레이아웃 템플릿
    ├── index.html          # 메인 페이지 템플릿
    ├── template_detail.html# 템플릿 상세 페이지
    ├── 404.html            # 404 오류 페이지
    ├── 500.html            # 500 오류 페이지
    ├── member/             # 회원 관련 템플릿
    │   ├── login.html      # 로그인 페이지
    │   ├── register.html   # 회원가입 페이지
    │   ├── profile.html    # 프로필 페이지
    │   └── change_password.html # 비밀번호 변경 페이지
    └── static/             # 정적 파일
        ├── css/            # CSS 파일
        ├── js/             # JavaScript 파일
        └── img/            # 이미지 파일
```

## 주요 모듈 설명

### 1. 설정 모듈 (config.py)
- 환경 변수 관리
- SQLAlchemy 객체 초기화
- 애플리케이션 설정값 정의

### 2. 회원 관리 모듈 (routes/member/)
- 사용자 인증 및 계정 관리 (로그인, 로그아웃, 회원가입)
- 프로필 조회 및 비밀번호 변경
- 계정 비활성화

### 3. API 연동 모듈 (api/government_api.py)
- 공공데이터포털 API 호출 및 응답 처리
- 템플릿 정보 추출 및 가공

### 4. 보고서 생성 모듈 (routes/drafts.py)
- 선택한 템플릿 기반 보고서 생성
- 토큰 비용 계산

### 5. 웹 클라이언트 모듈 (web/static/js/)
- 템플릿 검색 및 결과 표시
- 보고서 생성 요청 처리
- 사용자 인터페이스 상호작용

## 기술 스택

- **백엔드**: Flask, SQLAlchemy, Flask-Login
- **프론트엔드**: HTML, CSS, JavaScript, Tailwind CSS
- **데이터베이스**: SQLite
- **API**: 공공데이터포털 API

## 기여 방법

프로젝트 기여는 언제나 환영합니다. 다음 단계를 따라주세요:

1. 이 저장소를 포크(Fork)합니다.
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요. 