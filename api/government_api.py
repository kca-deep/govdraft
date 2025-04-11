"""
공공데이터포털 API 연동 모듈
정부 문서 데이터를 검색하고 처리하는 기능을 제공합니다.
"""

import json
import time
import requests
from config import Config
from utils.logging import logger
from utils.html_utils import clean_html_content, get_preview_content


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
    api_key = Config.PUBLIC_DATA_API_KEY
    if not api_key:
        logger.error("공공데이터포털 API 키가 설정되지 않았습니다.")
        return {"error": "API 키가 설정되지 않았습니다."}

    # 문서 유형 설정 확인
    if doc_type not in Config.DOC_TYPE_CONFIG:
        logger.error(f"지원하지 않는 문서 유형: {doc_type}")
        return {"error": f"지원하지 않는 문서 유형: {doc_type}"}

    config = Config.DOC_TYPE_CONFIG[doc_type]
    endpoint = config["endpoint"]
    url = f"{Config.API_BASE_URL}/{endpoint}"

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
    for attempt in range(Config.MAX_RETRIES):
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
            logger.warning(f"API 요청 타임아웃 (시도 {attempt+1}/{Config.MAX_RETRIES})")
            if attempt < Config.MAX_RETRIES - 1:
                time.sleep(Config.RETRY_DELAY)

        except requests.exceptions.ConnectionError:
            logger.warning(f"API 연결 오류 (시도 {attempt+1}/{Config.MAX_RETRIES})")
            if attempt < Config.MAX_RETRIES - 1:
                time.sleep(Config.RETRY_DELAY)

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
    logger.error(f"{Config.MAX_RETRIES}번의 시도 후 API 호출 실패")
    return {"error": f"{Config.MAX_RETRIES}번의 시도 후 API 호출 실패"}
