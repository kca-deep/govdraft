#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import datetime
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# 환경 변수 로드
load_dotenv()

# 로깅 설정
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(
    log_dir, f"govdraft_{datetime.datetime.now().strftime('%Y%m%d')}.log"
)
# 로그 레벨을 ERROR로 설정하여 에러 로그만 저장
log_level = "ERROR"

logging.basicConfig(
    filename=log_file,
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger("GovDraft")


def fetch_government_templates(
    keyword: str = "", page: int = 1, per_page: int = 10
) -> dict:
    """
    공공데이터포털 API를 호출하여 정부 문서 템플릿을 검색합니다.

    Args:
        keyword: 검색 키워드
        page: 페이지 번호
        per_page: 페이지당 결과 수

    Returns:
        API 응답 결과
    """
    api_key = os.getenv("PUBLIC_DATA_API_KEY")
    if not api_key:
        logger.error("공공데이터포털 API 키가 설정되지 않았습니다.")
        return {"error": "API 키가 설정되지 않았습니다."}

    try:
        # 공공데이터포털 API 엔드포인트 - 공공문서 API
        url = "http://apis.data.go.kr/1741000/publicDoc/getDocPress"

        # API 규격에 맞게 파라미터 수정
        # 디코딩된 인증키를 그대로 전달 - requests가 URL 인코딩을 수행
        params = {
            "serviceKey": api_key,  # 인증키 (디코딩된 상태)
            "pageNo": page,  # 페이지 번호
            "numOfRows": per_page,  # 페이지당 결과 수
            "type": "json",  # 응답 형식 (xml 또는 json)
        }

        # 키워드 검색 시 파라미터 추가
        if keyword:
            params["title"] = keyword  # 제목 검색 파라미터

        # 디버깅을 위한 요청 파라미터 로깅 (인증키는 일부만 표시)
        safe_params = params.copy()
        if "serviceKey" in safe_params:
            safe_params["serviceKey"] = safe_params["serviceKey"][:10] + "..."
        logger.info(f"API 요청 URL: {url}")
        logger.info(f"API 요청 파라미터: {safe_params}")

        # API 호출 시 타임아웃 및 재시도 설정
        response = requests.get(
            url,
            params=params,
            timeout=10,
            headers={"Accept": "application/json"},
            verify=True,  # SSL 인증서 검증
        )

        # 요청 URL 로깅 (디버깅용, 민감 정보 제외)
        request_url = response.url
        safe_url = request_url
        if "serviceKey=" in safe_url:
            key_start = safe_url.find("serviceKey=") + 11
            key_end = (
                safe_url.find("&", key_start)
                if "&" in safe_url[key_start:]
                else len(safe_url)
            )
            safe_url = safe_url[:key_start] + "..." + safe_url[key_end:]
        logger.info(f"실제 요청 URL: {safe_url}")

        # 응답 상태 코드 확인
        response.raise_for_status()

        # 응답 컨텐츠 로깅 (디버깅용, 일부만)
        if response.content:
            content_preview = response.content[:200].decode("utf-8", errors="replace")
            logger.info(f"API 응답 내용 미리보기: {content_preview}...")

        try:
            data = response.json()

            # API 응답 구조 처리 (공공데이터포털 표준 응답 구조)
            items = []
            total_count = 0

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

                    # items 처리 (항목이 있는 경우)
                    if "items" in body:
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
            return {"items": items, "totalCount": total_count}

        except json.JSONDecodeError:
            # JSON 파싱 실패 시 응답 내용 로깅
            logger.error(f"JSON 파싱 실패. 응답 내용: {response.text[:500]}...")
            return {"error": "API 응답을 JSON으로 파싱할 수 없습니다."}

    except requests.exceptions.RequestException as e:
        logger.error(f"공공데이터포털 API 호출 오류: {str(e)}")
        return {"error": f"API 호출 중 오류가 발생했습니다: {str(e)}"}


def save_templates_to_file(
    templates: list, output_file: str = "templates.json"
) -> bool:
    """
    템플릿 데이터를 파일로 저장합니다.

    Args:
        templates: 템플릿 목록
        output_file: 저장할 파일 경로

    Returns:
        저장 성공 여부
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        logger.info(f"{len(templates)}개의 템플릿을 {output_file}에 저장했습니다.")
        return True
    except Exception as e:
        logger.error(f"템플릿 저장 중 오류 발생: {str(e)}")
        return False


def fetch_all_templates(keyword: str = "", max_pages: int = 10) -> list:
    """
    여러 페이지에 걸쳐 모든 템플릿을 가져옵니다.

    Args:
        keyword: 검색 키워드
        max_pages: 최대 페이지 수

    Returns:
        모든 템플릿 목록
    """
    all_templates = []

    # 터미널 너비에 맞게 진행률 바 설정
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # 기본값

    # tqdm 진행률 바 설정
    progress_bar = tqdm(
        total=max_pages, desc="템플릿 가져오기", ncols=terminal_width - 20, unit="page"
    )

    for page in range(1, max_pages + 1):
        result = fetch_government_templates(keyword, page, per_page=50)

        if "error" in result:
            progress_bar.close()
            logger.error(f"템플릿 가져오기 실패: {result['error']}")
            return all_templates

        items = result.get("items", [])
        if not items:
            break

        all_templates.extend(items)
        progress_bar.update(1)

        # 마지막 페이지이면 종료
        if len(items) < 50:
            break

    progress_bar.close()
    logger.info(f"총 {len(all_templates)}개의 템플릿을 가져왔습니다.")
    return all_templates


def main():
    """
    메인 함수
    """
    print("정부 문서 템플릿 검색 도구")
    print("=" * 30)

    keyword = input("검색할 키워드를 입력하세요 (공백으로 두면 전체 검색): ")
    print(f"'{keyword}' 키워드로 검색을 시작합니다...")

    templates = fetch_all_templates(keyword)

    if templates:
        save_templates_to_file(templates)
        print(f"총 {len(templates)}개의 템플릿을 검색했습니다.")
        print("templates.json 파일에 저장되었습니다.")
    else:
        print("검색 결과가 없거나 오류가 발생했습니다.")


if __name__ == "__main__":
    main()
