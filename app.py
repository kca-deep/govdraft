"""
정부 문서 템플릿 검색 웹 애플리케이션
공공데이터포털 API를 활용하여 정부 문서를 검색하고 결과를 표시합니다.
"""

import os
import json
import logging
import datetime
import requests
import re
import time
from functools import lru_cache
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import tiktoken

# 환경 변수 로드
load_dotenv()

# 설정 값을 환경 변수에서 가져오기
API_BASE_URL = os.getenv("API_BASE_URL", "http://apis.data.go.kr/1741000/publicDoc")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
EXCHANGE_RATE = float(os.getenv("EXCHANGE_RATE", "1450"))

# 문서 유형별 엔드포인트와 필수 파라미터 정의
DOC_TYPE_CONFIG = {
    "press": {"endpoint": "getDocPress", "required_params": ["title", "manager"]},
    "speech": {"endpoint": "getDocSpeech", "required_params": ["title"]},
    "publication": {"endpoint": "getDocPublication", "required_params": ["title"]},
    "report": {"endpoint": "getDocReport", "required_params": ["title"]},
    "plan": {"endpoint": "getDocPlan", "required_params": ["title"]},
    "all": {"endpoint": "getDocAll", "required_params": ["title"]},
}


def setup_logging():
    """로깅 시스템을 초기화합니다."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(
        log_dir, f"govdraft_{datetime.datetime.now().strftime('%Y%m%d')}.log"
    )

    # 로그 핸들러 설정
    logger = logging.getLogger("GovDraft")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # 기존 핸들러 모두 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    try:
        # 로그 파일 초기화
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")  # 빈 파일로 초기화

        # 파일 핸들러 추가
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)  # 콘솔에는 ERROR 이상만 출력
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 로거가 상위 로거로 메시지를 전달하지 않도록 설정
        logger.propagate = False

        # 로그 시스템 초기화 메시지 기록
        logger.info("로깅 시스템이 초기화되었습니다.")

    except Exception as e:
        print(f"로그 설정 중 오류 발생: {str(e)}")
        # 기본 로깅으로 대체
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    return logger


# 로거 초기화
logger = setup_logging()

# Flask 애플리케이션 초기화
app = Flask(__name__, template_folder="templates")


# 모델별 가격 설정 (1K 토큰당 USD) - 캐싱 적용
@lru_cache(maxsize=16)
def get_model_prices():
    """모델별 가격 정보를 반환합니다. 캐싱을 적용하여 성능 최적화."""
    return {
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4o": {"input": 5.0, "output": 15.0},
    }


def calculate_token_cost(
    input_text: str, output_text: str, model: str = "gpt-4o-mini"
) -> dict:
    """
    입출력 텍스트의 토큰 수와 비용을 계산합니다.

    Args:
        input_text: 입력 텍스트
        output_text: 출력 텍스트
        model: 사용된 모델 이름

    Returns:
        토큰 수와 비용 정보가 담긴 사전
    """
    try:
        # 토큰 인코더 초기화
        encoding = tiktoken.encoding_for_model(model)

        # 토큰 수 계산
        input_tokens = len(encoding.encode(input_text))
        output_tokens = len(encoding.encode(output_text))
        total_tokens = input_tokens + output_tokens

        # 모델별 가격 정보 가져오기
        model_prices = get_model_prices()

        if model not in model_prices:
            logger.warning(
                f"알 수 없는 모델: {model}, 기본 모델(gpt-4o-mini) 가격을 사용합니다."
            )
            model = "gpt-4o-mini"

        # 비용 계산 (USD)
        input_cost_usd = (input_tokens / 1000) * model_prices[model]["input"]
        output_cost_usd = (output_tokens / 1000) * model_prices[model]["output"]
        total_cost_usd = input_cost_usd + output_cost_usd

        # 환율 적용
        total_cost_krw = total_cost_usd * EXCHANGE_RATE

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost_usd, 6),
            "cost_krw": round(total_cost_krw, 2),
            "model": model,
        }
    except Exception as e:
        logger.error(f"토큰 비용 계산 중 오류: {str(e)}")
        return {
            "error": f"토큰 비용 계산 중 오류: {str(e)}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "cost_krw": 0,
            "model": model,
        }


def clean_html_content(content: str) -> str:
    """
    HTML 태그를 제거하고 정제된 텍스트를 반환합니다.
    정부 문서 형식(□, ○ 등)의 구조를 보존합니다.

    Args:
        content: HTML 태그가 포함된 문자열

    Returns:
        정제된 문자열
    """
    if not content:
        return ""

    try:
        # 이미지 태그 제거
        content = re.sub(r"<img[^>]*>", "", content)

        # 스크립트 태그 제거
        content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL)

        # 스타일 태그 제거
        content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL)

        # HTML 주석 제거
        content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

        # 줄바꿈 유지를 위한 처리 (br 태그를 줄바꿈으로 변환)
        content = re.sub(r"<br\s*/?>", "\n", content)

        # 단락 태그를 줄바꿈으로 변환
        content = re.sub(r"<p[^>]*>", "", content)
        content = re.sub(r"</p>", "\n\n", content)

        # 표 처리 (간단한 처리)
        content = re.sub(r"<tr[^>]*>", "\n", content)
        content = re.sub(r"<td[^>]*>", " ", content)

        # 다른 HTML 태그 제거 (줄바꿈 정보 유지)
        content = re.sub(r"<[^>]*>", "", content)

        # 특수 기호 (□, ○) 앞뒤에 공백 확인
        content = re.sub(r"([□○])([^\s])", r"\1 \2", content)

        # 연속된 공백 처리 (줄바꿈은 유지)
        content = re.sub(r"[ \t]+", " ", content)

        # 빈 줄 여러 개를 최대 2개로 제한
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip()
    except Exception as e:
        logger.error(f"HTML 정제 중 오류: {str(e)}")
        return content


def get_preview_content(text, max_length=500):
    """
    텍스트 미리보기를 생성하되, 문단 단위로 잘라내어 구조를 보존합니다.

    Args:
        text: 원본 텍스트
        max_length: 최대 길이

    Returns:
        미리보기 텍스트
    """
    if not text or len(text) <= max_length:
        return text

    # □ 또는 ○ 기호로 시작하는 문단을 찾아 구조 보존
    paragraphs = re.split(r"(\n(?=[□○]))", text)
    result = ""

    for i, para in enumerate(paragraphs):
        if len(result + para) <= max_length:
            result += para
        else:
            break

    return result.strip() + "..." if len(text) > len(result) else result


def mask_api_key(url: str) -> str:
    """
    URL에서 API 키를 마스킹하여 로그에 안전하게 기록

    Args:
        url: 원본 URL

    Returns:
        API 키가 마스킹된 URL
    """
    if "serviceKey=" in url:
        key_start = url.find("serviceKey=") + 11
        key_end = url.find("&", key_start) if "&" in url[key_start:] else len(url)
        return url[:key_start] + "..." + url[key_end:]
    return url


def process_result_list(result_list, doc_type):
    """결과 리스트를 처리하여 표준화된 아이템으로 변환"""
    items = []

    if not isinstance(result_list, list):
        result_list = [result_list] if result_list else []

    for item in result_list:
        meta = item.get("meta", {})
        data_content = item.get("data", {})

        # 이미지 태그 제거
        text_content = data_content.get("text", "")
        cleaned_text = clean_html_content(text_content)

        # 기본 아이템 정보
        processed_item = {
            "id": meta.get("doc_id", ""),
            "title": meta.get("title", ""),
            "docType": meta.get("doc_type", ""),
            "date": meta.get("date", ""),
            "content": cleaned_text,
            "description": get_preview_content(cleaned_text, 500),
        }

        # 문서 유형별 필드 추가
        if doc_type == "press":
            processed_item.update(
                {
                    "time": meta.get("time", ""),
                    "ministry": meta.get("ministry", ""),
                    "department": meta.get("department", ""),
                    "manager": meta.get("manager", ""),
                    "relevantdepartments": meta.get("relevantdepartments", ""),
                }
            )
        elif doc_type in ["speech", "plan"]:
            processed_item.update(
                {
                    "place": meta.get("place", ""),
                    "person": meta.get("person", ""),
                }
            )
        elif doc_type == "publication":
            processed_item.update(
                {
                    "person": meta.get("person", ""),
                }
            )
        elif doc_type == "report":
            processed_item.update(
                {
                    "ministry": meta.get("ministry", ""),
                    "department": meta.get("department", ""),
                    "manager": meta.get("manager", ""),
                }
            )

        items.append(processed_item)

    return items


def process_items(items_data):
    """다른 형식의 items 데이터 처리"""
    items = []

    # 항목이 리스트인 경우
    if isinstance(items_data, list):
        items = items_data
    # 단일 항목인 경우 (dict) 리스트로 변환
    elif isinstance(items_data, dict) and "item" in items_data:
        item_data = items_data["item"]
        # item이 리스트인 경우
        if isinstance(item_data, list):
            items = item_data
        # item이 단일 객체인 경우
        elif isinstance(item_data, dict):
            items = [item_data]

    return items


def parse_api_response(data: dict, doc_type: str) -> dict:
    """
    API 응답을 파싱하여 필요한 데이터 추출

    Args:
        data: API 응답 데이터
        doc_type: 문서 유형

    Returns:
        처리된 결과
    """
    items = []
    total_count = 0
    page_no = 1
    num_of_rows = 10

    try:
        if "response" in data:
            response_data = data["response"]

            # 헤더 확인
            if "header" in response_data:
                header = response_data["header"]
                result_code = header.get("resultCode")
                result_msg = header.get("resultMsg")

                # 결과 코드가 성공(00)이 아닌 경우 오류 처리
                if result_code != "00":
                    logger.error(
                        f"API 오류 응답: 코드={result_code}, 메시지={result_msg}"
                    )
                    return {"error": f"API 오류: {result_msg} (코드: {result_code})"}

                logger.info(f"API 응답 성공: 코드={result_code}, 메시지={result_msg}")

            # 바디 처리
            if "body" in response_data:
                body = response_data["body"]
                total_count = body.get("totalCount", 0)
                page_no = body.get("pageNo", page_no)
                num_of_rows = body.get("numOfRows", num_of_rows)

                # resultList 처리 (회의/행사계획 API의 경우)
                if "resultList" in body:
                    items = process_result_list(body["resultList"], doc_type)
                # items 처리 (다른 API 형식의 경우)
                elif "items" in body:
                    items = process_items(body["items"])

        logger.info(f"API 응답 처리 완료: {len(items)}개 항목, 총 {total_count}개 결과")
        return {
            "items": items,
            "totalCount": total_count,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "docType": doc_type,
        }

    except Exception as e:
        logger.error(f"API 응답 파싱 중 오류: {str(e)}")
        return {"error": f"API 응답 파싱 중 오류: {str(e)}"}


def fetch_government_templates(
    keyword: str = "",
    page: int = 1,
    per_page: int = 10,
    doc_type: str = "press",
    manager: str = "",
) -> dict:
    """
    공공데이터포털 API를 호출하여 정부 문서 템플릿을 검색합니다.

    Args:
        keyword: 검색 키워드 (문서 제목)
        page: 페이지 번호
        per_page: 페이지당 결과 수
        doc_type: 문서 유형 (press, speech, publication, report, plan, all)
        manager: 담당자 이름 (보도자료 문서 유형에서 필수)

    Returns:
        API 응답 결과
    """
    api_key = os.getenv("PUBLIC_DATA_API_KEY")
    if not api_key:
        logger.error("공공데이터포털 API 키가 설정되지 않았습니다.")
        return {"error": "API 키가 설정되지 않았습니다."}

    # 문서 유형 설정 확인
    if doc_type not in DOC_TYPE_CONFIG:
        logger.error(f"지원하지 않는 문서 유형: {doc_type}")
        return {"error": f"지원하지 않는 문서 유형: {doc_type}"}

    config = DOC_TYPE_CONFIG[doc_type]
    endpoint = config["endpoint"]
    url = f"{API_BASE_URL}/{endpoint}"

    # 기본 파라미터 설정
    params = {
        "serviceKey": api_key,  # 인증키 (디코딩된 상태)
        "pageNo": page,  # 페이지 번호
        "numOfRows": per_page,  # 페이지당 결과 수
        "type": "json",  # 응답 형식 (xml 또는 json)
        "title": keyword if keyword else "",  # 필수 title 파라미터
    }

    # 필수 파라미터 확인 및 추가
    if "manager" in config["required_params"] and doc_type == "press":
        params["manager"] = manager

    # 키워드 로깅 (디버깅용)
    logger.info(f"검색 키워드: {keyword}")
    logger.info(f"문서 유형: {doc_type}")
    if manager:
        logger.info(f"담당자: {manager}")

    # 디버깅을 위한 요청 파라미터 로깅 (인증키는 일부만 표시)
    safe_params = params.copy()
    if "serviceKey" in safe_params:
        safe_params["serviceKey"] = safe_params["serviceKey"][:10] + "..."
    logger.info(f"API 요청 URL: {url}")
    logger.info(f"API 요청 파라미터: {safe_params}")

    # 재시도 메커니즘 구현
    for attempt in range(MAX_RETRIES):
        try:
            # API 호출
            response = requests.get(
                url,
                params=params,
                timeout=10,
                headers={"Accept": "application/json"},
                verify=True,  # SSL 인증서 검증
            )

            # 요청 URL 로깅 (디버깅용, 민감 정보 제외)
            request_url = response.url
            safe_url = mask_api_key(request_url)
            logger.info(f"실제 요청 URL: {safe_url}")

            # 상세 파라미터 로깅 (민감 정보 마스킹 처리)
            detailed_params = {k: v for k, v in params.items() if k != "serviceKey"}
            detailed_params["serviceKey"] = "..." if "serviceKey" in params else ""
            logger.info(
                f"상세 요청 파라미터 (로깅): {json.dumps(detailed_params, ensure_ascii=False)}"
            )

            # URL 쿼리 문자열 구성 (한글이 포함된 경우 URL 인코딩 확인)
            query_string = "&".join(
                [f"{k}={v}" for k, v in detailed_params.items() if k != "serviceKey"]
            )
            if "serviceKey" in params:
                query_string = (
                    f"serviceKey=...&{query_string}"
                    if query_string
                    else "serviceKey=..."
                )

            logger.info(f"완전한 API 호출 URL (마스킹됨): {url}?{query_string}")

            # 응답 상태 코드 확인
            response.raise_for_status()

            # 응답 컨텐츠 로깅 (디버깅용, 일부만)
            if response.content:
                content_preview = response.content[:200].decode(
                    "utf-8", errors="replace"
                )
                logger.info(f"API 응답 내용 미리보기: {content_preview}...")

            try:
                data = response.json()
                return parse_api_response(data, doc_type)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 응답 내용 로깅
                logger.error(f"JSON 파싱 실패. 응답 내용: {response.text[:500]}...")
                return {"error": "API 응답을 JSON으로 파싱할 수 없습니다."}

        except requests.exceptions.Timeout:
            logger.warning(f"API 요청 타임아웃 (시도 {attempt+1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        except requests.exceptions.ConnectionError:
            logger.warning(f"API 연결 오류 (시도 {attempt+1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        except requests.exceptions.HTTPError as e:
            status_code = (
                e.response.status_code if hasattr(e, "response") else "알 수 없음"
            )
            logger.error(f"API HTTP 오류: {status_code}, {str(e)}")
            return {"error": f"API HTTP 오류 ({status_code}): {str(e)}"}

        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 오류: {str(e)}")
            return {"error": f"API 요청 중 오류: {str(e)}"}

    # 모든 재시도 실패
    logger.error(f"{MAX_RETRIES}번의 시도 후 API 호출 실패")
    return {"error": f"{MAX_RETRIES}번의 시도 후 API 호출 실패"}


# 캐시를 활용한 API 응답 저장
template_cache = {}


# 라우트 설정
@app.route("/")
def index():
    """메인 페이지"""
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search_templates():
    """템플릿 검색 API"""
    keyword = request.args.get("keyword", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    doc_type = request.args.get("doc_type", "press")
    manager = request.args.get("manager", "")  # manager 파라미터 추가
    use_cache = request.args.get("use_cache", "true").lower() == "true"

    logger.info(
        f"템플릿 검색 요청: 키워드='{keyword}', 페이지={page}, 페이지당 결과수={per_page}, "
        f"문서유형={doc_type}, 담당자='{manager}'"
    )

    # 캐시 키 생성
    cache_key = f"{keyword}:{page}:{per_page}:{doc_type}:{manager}"  # 정렬은 클라이언트에서 하므로 캐시 키에서 제거

    # 캐시된 결과가 있고 캐시 사용이 활성화된 경우 캐시에서 반환
    if use_cache and cache_key in template_cache:
        logger.info(f"캐시된 결과 반환: {cache_key}")
        return jsonify(template_cache[cache_key])

    # API 호출
    result = fetch_government_templates(
        keyword, page, per_page, doc_type, manager
    )  # sort_by 인자 제거

    # 결과 캐싱 (오류가 없는 경우에만)
    if "error" not in result and use_cache:
        template_cache[cache_key] = result

    return jsonify(result)


# /api/templates/<template_id> 라우트는 프론트엔드에서 처리하므로 제거됨


@app.route("/api/token-cost", methods=["POST"])
def calculate_api_token_cost():
    """토큰 비용 계산 API"""
    try:
        data = request.get_json()
        input_text = data.get("input_text", "")
        output_text = data.get("output_text", "")
        model = data.get("model", "gpt-4o-mini")

        result = calculate_token_cost(input_text, output_text, model)
        return jsonify(result)
    except Exception as e:
        logger.error(f"토큰 비용 계산 API 오류: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route("/health")
def health_check():
    """서버 상태 확인용 엔드포인트"""
    return jsonify({"status": "ok", "timestamp": datetime.datetime.now().isoformat()})


@app.errorhandler(404)
def page_not_found(e):
    """404 에러 처리"""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """500 에러 처리"""
    logger.error(f"서버 오류: {str(e)}")
    return render_template("500.html"), 500


# /template/<template_id> 라우트는 프론트엔드 모달 처리로 인해 제거됨


@app.route("/api/drafts/generate", methods=["POST"])
def generate_draft():
    """선택한 템플릿을 기반으로 AI 보고서 생성 API"""
    try:
        data = request.get_json()

        if not data:
            logger.error("API 요청 본문이 비어 있음")
            return jsonify({"error": "요청 본문이 비어 있습니다."}), 400

        template_ids = data.get("template_ids", [])
        user_input = data.get("user_input", "")

        logger.info(
            f"보고서 생성 요청: 템플릿 ID={template_ids}, 입력 길이={len(user_input)}자"
        )

        # 필수 데이터 검증
        if not template_ids:
            logger.error("템플릿 ID가 제공되지 않음")
            return jsonify({"error": "템플릿 ID가 필요합니다."}), 400

        if not user_input:
            logger.error("사용자 입력이 제공되지 않음")
            return jsonify({"error": "보고서 정보가 필요합니다."}), 400

        # 선택된 템플릿 정보 수집
        selected_templates = []

        # 캐시된 데이터에서 템플릿 정보 찾기
        for key, data in template_cache.items():
            if "items" in data:
                for item in data["items"]:
                    if item.get("id") in template_ids:
                        selected_templates.append(item)
                        # 모든 템플릿을 찾았으면 루프 종료
                        if len(selected_templates) == len(template_ids):
                            break

        # 캐시에서 템플릿을 찾지 못한 경우 (캐시 만료 또는 새로운 세션)
        missing_templates = [
            tid
            for tid in template_ids
            if tid not in [t.get("id") for t in selected_templates]
        ]

        if missing_templates:
            logger.warning(f"캐시에서 찾을 수 없는 템플릿: {missing_templates}")
            return (
                jsonify(
                    {
                        "error": "일부 템플릿 정보를 찾을 수 없습니다. 검색을 다시 실행해주세요."
                    }
                ),
                404,
            )

        # TODO: 실제 AI 모델을 통한 보고서 생성 기능 구현
        # 현재는 예시 응답 반환

        # 입력과 템플릿 내용을 기반으로 토큰 비용 계산
        template_titles = [t.get("title", "") for t in selected_templates]
        template_contents = [t.get("content", "") for t in selected_templates]

        combined_input = (
            user_input
            + "\n\n"
            + "\n\n".join(template_titles)
            + "\n\n"
            + "\n\n".join(template_contents[:3])
        )  # 너무 길지 않게 처음 3개만 사용
        example_output = f"""# {user_input.split(',')[0] if ',' in user_input else '보고서 제목'}

## 개요
{user_input}

## 주요 내용
1. 첫 번째 주요 내용
2. 두 번째 주요 내용
3. 세 번째 주요 내용

## 참고 문서
{', '.join(template_titles)}

## 작성일
{datetime.datetime.now().strftime('%Y-%m-%d')}
"""

        # 토큰 비용 계산
        token_cost = calculate_token_cost(
            combined_input[:5000], example_output, "gpt-4o-mini"
        )

        # 응답 생성
        response = {
            "id": f"draft_{int(time.time())}",
            "created_at": datetime.datetime.now().isoformat(),
            "template_ids": template_ids,
            "user_input": user_input,
            "token_info": token_cost,
            "content": example_output,
            "status": "success",
        }

        logger.info(
            f"보고서 생성 완료: draft_id={response['id']}, 토큰={token_cost.get('total_tokens', 0)}"
        )
        return jsonify(response)

    except Exception as e:
        logger.error(f"보고서 생성 중 오류: {str(e)}")
        return jsonify({"error": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"}), 500


if __name__ == "__main__":
    # 웹 애플리케이션 실행
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Flask 웹 애플리케이션을 {port} 포트에서 시작합니다.")
    print(f"Flask 웹 애플리케이션을 http://localhost:{port} 에서 실행 중입니다.")
    app.run(debug=True, host="0.0.0.0", port=port)
