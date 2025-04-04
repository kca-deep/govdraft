import os
import json
import logging
import datetime
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import tiktoken
import re  # 정규식 모듈 추가

# 환경 변수 로드
load_dotenv()

# 로깅 설정
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(
    log_dir, f"govdraft_{datetime.datetime.now().strftime('%Y%m%d')}.log"
)
# 로그 레벨을 환경 변수에서 가져오되 ERROR 레벨로 설정
log_level = "ERROR"  # 항상 ERROR 레벨 로그만 기록하도록 설정

logging.basicConfig(
    filename=log_file,
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger("GovDraft")

# Flask 애플리케이션 초기화
app = Flask(__name__, template_folder="templates")


# OpenAI 토큰 비용 계산 함수
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
    # 토큰 인코더 초기화
    encoding = tiktoken.encoding_for_model(model)

    # 토큰 수 계산
    input_tokens = len(encoding.encode(input_text))
    output_tokens = len(encoding.encode(output_text))
    total_tokens = input_tokens + output_tokens

    # 모델별 가격 설정 (1K 토큰당 USD)
    # 최신 가격 정보는 OpenAI 공식 사이트에서 확인해야 함
    model_prices = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},  # 예시 가격
        "gpt-4o": {"input": 5.0, "output": 15.0},  # 예시 가격
    }

    if model not in model_prices:
        logger.warning(
            f"알 수 없는 모델: {model}, 기본 모델(gpt-4o-mini) 가격을 사용합니다."
        )
        model = "gpt-4o-mini"

    # 비용 계산 (USD)
    input_cost_usd = (input_tokens / 1000) * model_prices[model]["input"]
    output_cost_usd = (output_tokens / 1000) * model_prices[model]["output"]
    total_cost_usd = input_cost_usd + output_cost_usd

    # 환율 적용 (1 USD = 1450 KRW)
    exchange_rate = 1450
    total_cost_krw = total_cost_usd * exchange_rate

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost_usd": total_cost_usd,
        "cost_krw": total_cost_krw,
        "model": model,
    }


# HTML 태그 제거 함수
def clean_html_content(content: str) -> str:
    """
    HTML 태그를 제거하고 정제된 텍스트를 반환합니다.

    Args:
        content: HTML 태그가 포함된 문자열

    Returns:
        정제된 문자열
    """
    # 이미지 태그 제거
    content = re.sub(r"<img[^>]*>", "", content)

    # 필요 시 다른 HTML 태그 제거 가능
    # content = re.sub(r'<[^>]*>', '', content)

    return content


# 공공데이터포털 API 호출 함수
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

    # API 엔드포인트 선택
    endpoints = {
        "press": "getDocPress",
        "speech": "getDocSpeech",
        "publication": "getDocPublication",
        "report": "getDocReport",
        "plan": "getDocPlan",
        "all": "getDocAll",
    }

    if doc_type not in endpoints:
        logger.error(f"지원하지 않는 문서 유형: {doc_type}")
        return {"error": f"지원하지 않는 문서 유형: {doc_type}"}

    endpoint = endpoints[doc_type]

    try:
        # 공공데이터포털 API 엔드포인트
        url = f"http://apis.data.go.kr/1741000/publicDoc/{endpoint}"

        # 기본 파라미터 설정
        params = {
            "serviceKey": api_key,  # 인증키 (디코딩된 상태)
            "pageNo": page,  # 페이지 번호
            "numOfRows": per_page,  # 페이지당 결과 수
            "type": "json",  # 응답 형식 (xml 또는 json)
        }

        # 필수 title 파라미터 추가
        params["title"] = keyword if keyword else ""

        # 추가 파라미터 (문서 유형별 필수 파라미터)
        today = datetime.datetime.now().strftime("%Y%m%d")
        start_date = datetime.datetime.now().replace(day=1).strftime("%Y%m%d")

        # 문서 유형별 추가 필수 파라미터 설정
        if doc_type == "press":
            # 보도자료: 추가로 manager 필요
            params["manager"] = manager if manager else ""
        elif doc_type == "speech":
            # 연설문: title만 필요 (이미 설정됨)
            pass
        elif doc_type == "publication":
            # 발간사: title만 필요 (이미 설정됨)
            pass
        elif doc_type == "report":
            # 정책보고서: title만 필요 (이미 설정됨)
            pass
        elif doc_type == "plan":
            # 회의·행사계획: title만 필요 (이미 설정됨)
            pass
        elif doc_type == "all":
            # 공문서 전체: 기본 파라미터만 필요
            pass

        # 디버깅을 위한 요청 파라미터 로깅 (인증키는 일부만 표시)
        safe_params = params.copy()
        if "serviceKey" in safe_params:
            safe_params["serviceKey"] = safe_params["serviceKey"][:10] + "..."
        logger.info(f"API 요청 URL: {url}")
        logger.info(f"API 요청 파라미터: {safe_params}")

        # 완전한 파라미터 로깅 (개발 목적으로만 사용하고 나중에 제거해야 함)
        full_params_log = []
        for key, value in params.items():
            # serviceKey를 포함한 모든 파라미터 표시
            full_params_log.append(f"{key}={value}")
        full_url = f"{url}?{'&'.join(full_params_log)}"
        logger.info(f"전체 API 요청 URL과 파라미터(serviceKey 포함): {full_url}")

        # API 호출 시 타임아웃 및 재시도 설정
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={"Accept": "application/json"},
            verify=True,  # SSL 인증서 검증
        )

        # 요청 URL 로깅 (전체 URL 포함)
        request_url = response.url
        logger.info(f"실제 요청 URL(전체): {request_url}")

        # 응답 상태 코드 확인
        response.raise_for_status()

        # 응답 컨텐츠 로깅 (디버깅용, 일부만)
        if response.content:
            content_preview = response.content[:500].decode("utf-8", errors="replace")
            logger.info(f"API 응답 내용 미리보기: {content_preview}...")
            # 전체 응답 기록 (개발 디버깅 용도)
            full_response = response.content.decode("utf-8", errors="replace")
            logger.info(f"API 전체 응답 내용: {full_response}")

        try:
            data = response.json()

            # API 응답 구조 처리 (공공데이터포털 표준 응답 구조)
            items = []
            total_count = 0
            page_no = 1
            num_of_rows = per_page

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
                        return {
                            "error": f"API 오류: {result_msg} (코드: {result_code})"
                        }

                    logger.info(
                        f"API 응답 성공: 코드={result_code}, 메시지={result_msg}"
                    )

                # 바디 처리
                if "body" in response_data:
                    body = response_data["body"]
                    total_count = body.get("totalCount", 0)
                    page_no = body.get("pageNo", page)
                    num_of_rows = body.get("numOfRows", per_page)

                    # resultList 처리 (회의/행사계획 API의 경우)
                    if "resultList" in body:
                        result_list = body["resultList"]

                        if isinstance(result_list, list):
                            # 응답 형식에 맞게 아이템 구성
                            for item in result_list:
                                meta = item.get("meta", {})
                                data_content = item.get("data", {})

                                # 이미지 태그 제거
                                text_content = data_content.get("text", "")
                                cleaned_text = clean_html_content(text_content)

                                # 문서 유형별 처리
                                processed_item = {
                                    "id": meta.get("doc_id", ""),
                                    "title": meta.get("title", ""),
                                    "docType": meta.get("doc_type", ""),
                                    "date": meta.get("date", ""),
                                    "content": cleaned_text,
                                    "description": (
                                        cleaned_text[:500] + "..."
                                        if len(cleaned_text) > 500
                                        else cleaned_text
                                    ),
                                }

                                # 문서 유형별 필드 추가
                                if doc_type == "press":
                                    processed_item.update(
                                        {
                                            "time": meta.get("time", ""),
                                            "ministry": meta.get("ministry", ""),
                                            "department": meta.get("department", ""),
                                            "manager": meta.get("manager", ""),
                                            "relevantdepartments": meta.get(
                                                "relevantdepartments", ""
                                            ),
                                        }
                                    )
                                elif doc_type == "speech":
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
                                elif doc_type == "plan":
                                    processed_item.update(
                                        {
                                            "place": meta.get("place", ""),
                                            "person": meta.get("person", ""),
                                        }
                                    )

                                items.append(processed_item)

                    # items 처리 (다른 API 형식의 경우)
                    elif "items" in body:
                        items_data = body["items"]

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

            logger.info(
                f"API 응답 처리 완료: {len(items)}개 항목, 총 {total_count}개 결과"
            )
            return {
                "items": items,
                "totalCount": total_count,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "docType": doc_type,
            }

        except json.JSONDecodeError:
            # JSON 파싱 실패 시 응답 내용 로깅
            logger.error(f"JSON 파싱 실패. 응답 내용: {response.text[:500]}...")
            return {"error": "API 응답을 JSON으로 파싱할 수 없습니다."}

    except requests.exceptions.RequestException as e:
        logger.error(f"공공데이터포털 API 호출 오류: {str(e)}")
        return {"error": f"API 호출 중 오류가 발생했습니다: {str(e)}"}


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

    logger.info(
        f"템플릿 검색 요청: 키워드='{keyword}', 페이지={page}, 페이지당 결과수={per_page}, 문서유형={doc_type}, 담당자='{manager}'"
    )

    result = fetch_government_templates(keyword, page, per_page, doc_type, manager)
    return jsonify(result)


@app.route("/template/<template_id>")
def template_detail(template_id):
    """템플릿 상세 정보 페이지"""
    logger.info(f"템플릿 상세 정보 요청: 템플릿 ID={template_id}")
    # 실제 구현에서는 템플릿 ID로 해당 템플릿의 상세 정보를 가져와야 함
    return render_template("template_detail.html", template_id=template_id)


if __name__ == "__main__":
    # 개발 환경에서만 디버그 모드로 실행
    app.run(debug=os.getenv("LOG_LEVEL") == "INFO", port=5000)
