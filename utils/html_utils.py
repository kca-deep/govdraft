"""
HTML 처리 유틸리티
HTML 콘텐츠 처리 및 변환 관련 기능을 제공합니다.
"""

import re
from bs4 import BeautifulSoup
from utils.logging import logger


def clean_html_content(html_content: str) -> str:
    """
    BeautifulSoup를 사용하여 HTML 내용을 처리합니다.
    <table> 태그는 유지하고, 나머지 텍스트는 줄바꿈을 반영하여 추출합니다.

    Args:
        html_content: HTML 태그가 포함된 문자열

    Returns:
        처리된 문자열 (표는 HTML, 나머지는 텍스트)
    """
    if not html_content:
        return ""

    try:
        soup = BeautifulSoup(html_content, "lxml")
        output_parts = []

        # body 태그가 있으면 body의 자식들을, 없으면 전체 자식들을 순회
        elements_to_process = soup.body.children if soup.body else soup.children

        for element in elements_to_process:
            if element.name == "table":
                # 테이블 태그는 HTML 그대로 추가
                output_parts.append(str(element))
            elif hasattr(element, "get_text"):
                # 다른 태그는 텍스트 추출 (separator='\n'으로 줄바꿈 반영 시도)
                text = element.get_text(separator="\n", strip=True)
                if text:  # 빈 텍스트는 추가하지 않음
                    output_parts.append(text)
            elif isinstance(element, str) and element.strip():
                # 순수 텍스트 노드 처리 (공백만 있는 노드 제외)
                output_parts.append(element.strip())

        # 각 부분을 두 줄 바꿈으로 연결하여 최종 결과 생성
        # 테이블과 텍스트 블록 사이에 적절한 간격을 줌
        return "\n\n".join(output_parts).strip()

    except Exception as e:
        logger.error(f"BeautifulSoup HTML 처리 중 오류: {str(e)}")
        # 오류 발생 시 원본 반환 또는 기본 텍스트 추출 시도
        try:
            # 기본적인 텍스트 추출 시도
            soup = BeautifulSoup(html_content, "lxml")
            return soup.get_text(separator="\n", strip=True)
        except Exception:
            return html_content  # 이것도 실패하면 원본 반환


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
