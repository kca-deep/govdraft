"""
OpenAI API 통합 모듈
OpenAI API를 활용하여 자연어 처리 및 텍스트 생성 기능을 제공합니다.
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Union
from datetime import datetime
import openai
from dotenv import load_dotenv
from config import Config
from utils.token_utils import calculate_token_cost
from utils.logging import logger

# 환경 변수 로드
load_dotenv()

# OpenAI API 관련 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", Config.OPENAI_API_KEY)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", Config.OPENAI_MODEL)
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

# API 키 확인 및 설정
if not OPENAI_API_KEY:
    logger.error(
        "OpenAI API 키가 설정되지 않았습니다. 환경 변수 OPENAI_API_KEY를 확인해주세요."
    )
else:
    openai.api_key = OPENAI_API_KEY
    logger.info(f"OpenAI 모델: {OPENAI_MODEL}")


def call_openai_api(
    messages: List[Dict[str, str]],
    model: str = OPENAI_MODEL,
    temperature: float = 0.2,
    max_tokens: int = None,
    max_retries: int = 3,
    initial_retry_delay: float = 1.0,
) -> Tuple[Dict[str, Any], Dict[str, Union[int, float, str]]]:
    """
    OpenAI API를 호출하여 응답을 받아옵니다.

    Args:
        messages: 메시지 리스트
        model: 사용할 모델
        temperature: 생성 다양성 조절
        max_tokens: 최대 생성 토큰 수
        max_retries: 최대 재시도 횟수
        initial_retry_delay: 초기 재시도 지연 시간(초)

    Returns:
        응답 내용과 토큰 사용량 정보를 포함한 튜플
    """
    retry_delay = initial_retry_delay
    request_args = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    if max_tokens:
        request_args["max_tokens"] = max_tokens

    start_time = time.time()

    for attempt in range(max_retries):
        try:
            logger.info(
                f"OpenAI API 호출 시작: 모델={model}, 시도={attempt + 1}/{max_retries}"
            )

            response = openai.ChatCompletion.create(**request_args)
            result = {
                "content": response.choices[0].message.content.strip(),
                "usage": response.usage,
            }

            input_tokens = result["usage"]["prompt_tokens"]
            output_tokens = result["usage"]["completion_tokens"]
            token_info = calculate_token_cost(input_tokens, output_tokens, model)

            processing_time = time.time() - start_time
            logger.info(
                f"OpenAI API 응답 수신: 처리 시간={processing_time:.2f}초, "
                f"입력 토큰={input_tokens}, 출력 토큰={output_tokens}, "
                f"비용(KRW)={token_info['cost_krw']:.2f}원"
            )

            return result, token_info

        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                logger.warning(
                    f"API 속도 제한, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("API 속도 제한으로 최대 재시도 횟수 초과")
                raise

        except openai.error.APIError as e:
            logger.error(f"OpenAI API 오류: {str(e)}")
            if attempt < max_retries - 1:
                logger.warning(
                    f"API 오류, {retry_delay}초 후 재시도 ({attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            raise


def analyze_document_with_ai(text: str) -> Dict[str, Any]:
    """
    OpenAI를 사용하여 문서를 분석합니다.

    Args:
        text: 분석할 문서 내용

    Returns:
        Dict: 분석 결과 (구조, 어조, 핵심 키워드 등)
    """
    # HTML 태그 제거 및 텍스트 정제
    clean_text = re.sub(r"<.*?>", " ", text) if text else ""
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # 토큰 한도를 고려하여 텍스트 길이 제한
    max_text_length = 15000
    if len(clean_text) > max_text_length:
        clean_text = clean_text[:max_text_length] + "..."

    prompt = [
        {
            "role": "system",
            "content": """문서를 분석하여 다음 카테고리에 따라 JSON 형식으로 결과를 제공하세요:
1. 문서 구조 (paragraph_count, sentence_count, avg_sentence_length, has_table, has_list, has_image)
2. 어조 분석 (formality, sentiment, objectivity)
3. 핵심 키워드 (10개)
4. 요약 (200자 이내)""",
        },
        {"role": "user", "content": clean_text},
    ]

    try:
        result, token_info = call_openai_api(prompt)
        content = result["content"]

        try:
            # JSON 직접 파싱 시도
            analysis_result = json.loads(content)
            analysis_result["token_info"] = token_info
            return analysis_result
        except json.JSONDecodeError:
            # JSON 부분 추출 시도
            json_pattern = re.compile(r"({.*})", re.DOTALL)
            match = json_pattern.search(content)
            if match and (json_str := match.group(1)):
                try:
                    analysis_result = json.loads(json_str)
                    analysis_result["token_info"] = token_info
                    return analysis_result
                except json.JSONDecodeError:
                    pass

            # 기본 응답 생성
            return {
                "structure": {
                    "paragraph_count": 0,
                    "sentence_count": 0,
                    "avg_sentence_length": 0,
                    "has_table": "<table>" in text.lower(),
                    "has_list": any(
                        tag in text.lower() for tag in ["<ul>", "<ol>", "<li>"]
                    ),
                    "has_image": "<img" in text.lower(),
                },
                "tone": {"formality": 0.5, "sentiment": 0, "objectivity": 0.5},
                "keywords": [],
                "summary": "분석 실패",
                "token_info": token_info,
                "raw_response": content,
            }

    except Exception as e:
        logger.error(f"문서 분석 중 오류: {str(e)}")
        return {
            "structure": {
                "paragraph_count": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0,
                "has_table": "<table>" in text.lower(),
                "has_list": any(
                    tag in text.lower() for tag in ["<ul>", "<ol>", "<li>"]
                ),
                "has_image": "<img" in text.lower(),
            },
            "tone": {"formality": 0.5, "sentiment": 0, "objectivity": 0.5},
            "keywords": [],
            "summary": "분석 실패",
            "error": str(e),
        }


def analyze_templates(
    template_contents: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Union[int, float, str]]]:
    """
    여러 문서 템플릿을 분석하여 표준 항목과 내용을 추출합니다.

    Args:
        template_contents: 분석할 템플릿 내용 목록

    Returns:
        분석 결과와 토큰 사용량 정보를 포함한 튜플
    """
    try:
        logger.info(f"템플릿 분석 시작: {len(template_contents)}개 템플릿")

        # 템플릿 내용을 문자열로 변환
        templates_text = "\n\n===== 템플릿 구분선 =====\n\n".join(
            f"템플릿 ID: {item.get('id', 'unknown')}\n제목: {item.get('title', '제목 없음')}\n내용:\n{item.get('content', '')}"
            for item in template_contents
        )

        messages = [
            {
                "role": "system",
                "content": """당신은 문서 템플릿 분석 전문가입니다. 제공된 정부 문서 템플릿을 분석하여 다음 작업을 수행하세요:
1. 각 템플릿의 주요 표준 항목을 식별하고 구조화
2. 각 항목에 대한 설명과 예시 제공
3. 좋은 작성 방법에 대한 간략한 조언 추가
4. 템플릿의 핵심 키워드 추출""",
            },
            {
                "role": "user",
                "content": f"다음 템플릿을 분석하세요:\n\n{templates_text}",
            },
        ]

        result, token_info = call_openai_api(messages)

        # JSON 응답 추출 및 파싱
        content = result["content"]
        try:
            # JSON 직접 파싱 시도
            analysis_result = json.loads(content)
        except json.JSONDecodeError:
            # JSON 코드 블록에서 추출 시도
            json_pattern = r"```(?:json)?\n([\s\S]*?)\n```"
            if match := re.search(json_pattern, content):
                try:
                    analysis_result = json.loads(match.group(1))
                except json.JSONDecodeError:
                    analysis_result = {
                        "templates": [],
                        "error": "분석 결과를 파싱할 수 없음",
                    }
            else:
                analysis_result = {
                    "templates": [],
                    "error": "분석 결과를 파싱할 수 없음",
                }

        logger.info(f"템플릿 분석 완료: {len(template_contents)}개 템플릿")
        return analysis_result, token_info

    except Exception as e:
        logger.error(f"템플릿 분석 중 오류 발생: {str(e)}")
        return {"error": f"템플릿 분석 중 오류: {str(e)}"}, {"error": str(e)}


def analyze_templates_from_json(json_file_path: str, output_file_path: str) -> bool:
    """
    JSON 파일에서 템플릿 데이터를 읽고 분석 결과를 저장합니다.

    Args:
        json_file_path: 템플릿 데이터가 저장된 JSON 파일 경로
        output_file_path: 분석 결과를 저장할 JSON 파일 경로

    Returns:
        bool: 성공 여부
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            templates = json.load(f)

        if not isinstance(templates, list) or not templates:
            logger.error(
                f"템플릿 데이터가 없거나 유효하지 않은 형식입니다: {json_file_path}"
            )
            return False

        # 템플릿 기본 필드 정규화
        for i, template in enumerate(templates):
            template.setdefault("id", f"template_{i+1}")
            template.setdefault("title", template.get("제목", "제목 없음"))
            template.setdefault("content", template.get("내용", ""))

        # 템플릿 분석 및 결과 저장
        analysis_results, _ = analyze_templates(templates)
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        logger.info(
            f"템플릿 분석 완료: {len(templates)}개 분석됨, 결과 저장: {output_file_path}"
        )
        return True

    except Exception as e:
        logger.error(f"템플릿 분석 중 오류: {str(e)}")
        return False


def generate_draft(
    user_input: Dict[str, str], selected_templates: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], Dict[str, Union[int, float, str]]]:
    """
    사용자 입력과 선택된 템플릿을 기반으로 문서 초안을 생성합니다.

    Args:
        user_input: 사용자가 입력한 보고서 정보
        selected_templates: 선택된 템플릿 목록

    Returns:
        생성된 초안 결과와 토큰 사용량 정보를 포함한 튜플
    """
    logger.info(f"초안 생성 시작: {len(selected_templates)}개 템플릿 사용")
    start_time = time.time()

    try:
        # 템플릿 내용 추출 및 요구사항 구성
        template_contents = [
            f"### {template.get('title', '제목 없음')}\n{template.get('content', '')}"
            for template in selected_templates
        ]

        user_requirements = [
            f"{key}: {value}" for key, value in user_input.items() if value
        ]

        messages = [
            {
                "role": "system",
                "content": """당신은 한국의 정부 문서 작성을 돕는 전문가입니다. 
사용자가 제공한 템플릿과 요구사항을 기반으로 고품질의 보고서를 작성해주세요.
주어진 템플릿의 구조와 형식을 참고하되, 요구사항에 맞게 내용을 조정하세요.""",
            },
            {
                "role": "user",
                "content": f"""## 사용자 요구사항
{chr(10).join(user_requirements)}

## 참고 템플릿
{chr(10).join(template_contents)}

위 요구사항과 참고 템플릿을 기반으로 보고서를 작성해주세요.""",
            },
        ]

        result, token_info = call_openai_api(messages, temperature=0.7, max_tokens=2000)

        response = {
            "title": user_input.get("title", "제목 없음"),
            "content": result["content"],
            "timestamp": datetime.now().isoformat(),
        }

        processing_time = time.time() - start_time
        logger.info(
            f"초안 생성 완료: {processing_time:.2f}초 소요, "
            f"{token_info['total_tokens']}개 토큰 사용"
        )

        return response, token_info

    except Exception as e:
        logger.error(f"초안 생성 중 오류 발생: {str(e)}")
        return {
            "title": user_input.get("title", "제목 없음"),
            "error": f"초안 생성 중 오류: {str(e)}",
            "content": "",
            "timestamp": datetime.now().isoformat(),
        }, {"error": str(e)}
