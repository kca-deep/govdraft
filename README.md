# 정부 문서 템플릿 검색기 (GovDraft)

공공데이터포털 API를 활용하여 정부 문서를 검색하고 결과를 표시하는 웹 애플리케이션입니다.

## 주요 기능

- 보도자료, 연설문, 간행물, 보고서, 계획서 등 다양한 정부 문서 검색
- 문서 유형별 검색 필터링
- 사용자 친화적인 인터페이스로 검색 결과 표시
- 페이지네이션을 통한 대량의 검색 결과 탐색
- 토큰 비용 계산 API (OpenAI GPT 모델 사용 시)

## 기술 스택

- **프론트엔드**: HTML, JavaScript, Tailwind CSS, shadcn UI
- **백엔드**: Python, Flask
- **API**: 공공데이터포털 오픈 API
- **기타 도구**: tiktoken (토큰 계산), dotenv (환경변수 관리)

## 설치 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/yourusername/govdraft.git
   cd govdraft
   ```

2. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정
   - `.env.example` 파일을 `.env`로 복사하고 필요한 값을 입력
   ```bash
   cp .env.example .env
   # .env 파일을 편집하여 API 키 등 필요한 환경 변수 설정
   ```

## 사용 방법

1. 애플리케이션 실행
   ```bash
   python app.py
   ```

2. 웹 브라우저에서 접속
   - 기본 URL: `http://localhost:5000`

3. 검색 기능 사용
   - 키워드 입력 및 문서 유형 선택 후 검색
   - 결과 목록에서 원하는 문서 선택하여 상세 내용 확인

## API 엔드포인트

- `GET /`: 메인 검색 페이지
- `GET /search`: 템플릿 검색 API
  - 파라미터: `keyword`, `page`, `per_page`, `doc_type`, `manager`
- `GET /template/<template_id>`: 템플릿 상세 정보 페이지
- `POST /api/token-cost`: 토큰 비용 계산 API
- `GET /health`: 서버 상태 확인

## 프로젝트 구조

```
govdraft/
├── app.py                  # 애플리케이션 진입점 (애플리케이션 팩토리 함수)
├── config.py               # 설정 및 환경 변수 관리
├── api/                    # API 연동 모듈
│   ├── __init__.py
│   └── government_api.py   # 공공데이터포털 API 연동
├── routes/                 # 라우트 핸들러
│   ├── __init__.py         # 블루프린트 등록
│   ├── main.py             # 메인 라우트 (기본, 검색, 토큰 계산, 오류 처리)
│   └── drafts.py           # 보고서 생성 관련 라우트
├── utils/                  # 유틸리티 함수
│   ├── __init__.py
│   ├── logging.py          # 로깅 설정
│   ├── html_utils.py       # HTML 처리 유틸리티
│   └── token_utils.py      # 토큰 계산 관련 유틸리티
├── web/                    # HTML 템플릿 및 정적 파일 디렉토리
│   ├── base.html           # 기본 레이아웃 템플릿
│   ├── index.html          # 메인 검색 페이지
│   ├── template_detail.html  # 템플릿 상세 페이지
│   ├── 404.html            # 404 오류 페이지
│   ├── 500.html            # 500 오류 페이지
│   └── static/             # 정적 파일 (CSS, JS, 이미지)
│       ├── css/            # CSS 파일
│       └── js/             # JavaScript 파일
├── logs/                   # 로그 파일 디렉토리
├── .env                    # 환경 변수 파일
├── requirements.txt        # 프로젝트 의존성
├── README.md               # 프로젝트 문서
└── LICENSE                 # 라이센스 정보
```

## 라이센스

이 프로젝트는 MIT 라이센스에 따라 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.

## 문의

프로젝트에 관한 문의나 버그 리포트는 이슈 트래커를 통해 제출해 주세요. 