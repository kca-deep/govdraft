"""
OpenAI API 통합 모듈
OpenAI API를 활용하여 자연어 처리 및 텍스트 생성 기능을 제공합니다.
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Tuple, Optional, Union
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
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", Config.OPENAI_MODEL)
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초 단위

# API 키 설정
openai.api_key = OPENAI_API_KEY


# HTML 태그 제거 함수
def remove_html_tags(text: str) -> str:
    """HTML 태그를 제거하고 텍스트만 추출합니다."""
    if not text:
        return ""
    clean_text = re.sub(r"<.*?>", " ", text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    return clean_text


def call_openai_api(
    messages_or_prompt: Union[List[Dict[str, str]], str],
    model: str = OPENAI_MODEL,
    temperature: float = 0.2,
    max_tokens: Optional[int] = None,
    max_retries: int = 3,
    initial_retry_delay: float = 1.0,
) -> Tuple[Dict[str, Any], Dict[str, Union[int, float, str]]]:
    """
    OpenAI API를 호출하여 응답을 받아옵니다.
    messages 형식과 단일 prompt 문자열 두 가지 형식을 모두 지원합니다.

    Args:
        messages_or_prompt: 메시지 리스트 또는 단일 프롬프트 문자열
        model: 사용할 모델 (기본값: Config.OPENAI_MODEL)
        temperature: 생성 다양성 조절 (기본값: 0.2)
        max_tokens: 최대 생성 토큰 수 (기본값: None, API 기본값 사용)
        max_retries: 최대 재시도 횟수 (기본값: 3)
        initial_retry_delay: 초기 재시도 지연 시간(초) (기본값: 1.0)

    Returns:
        응답 내용과 토큰 사용량 정보를 포함한 튜플
    """
    retry_delay = initial_retry_delay
    is_messages_format = isinstance(messages_or_prompt, list)

    # 메시지 또는 프롬프트 준비
    if is_messages_format:
        messages = messages_or_prompt
        request_args = {"messages": messages}
    else:
        prompt = messages_or_prompt
        request_args = {"prompt": prompt}

    # 공통 API 요청 인자 설정
    request_args.update(
        {
            "model": model,
            "temperature": temperature,
        }
    )

    if max_tokens:
        request_args["max_tokens"] = max_tokens

    # 요청 전 입력 토큰 수 계산
    if is_messages_format:
        # 메시지 형식의 입력을 문자열로 변환하여 토큰 계산
        input_text = json.dumps(messages, ensure_ascii=False)
    else:
        input_text = prompt

    start_time = time.time()

    for attempt in range(max_retries):
        try:
            logger.info(
                f"OpenAI API 호출 시작: 모델={model}, 시도={attempt + 1}/{max_retries}"
            )

            # API 요청
            if is_messages_format:
                response = openai.ChatCompletion.create(**request_args)
                result = {
                    "content": response.choices[0].message.content.strip(),
                    "usage": response.usage,
                }
            else:
                response = openai.Completion.create(**request_args)
                result = {
                    "content": response.choices[0].text.strip(),
                    "usage": response.usage,
                }

            # 토큰 사용량 계산
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
                retry_delay *= 2  # 지수 백오프
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
    # HTML 태그 제거
    clean_text = remove_html_tags(text)

    # 너무 긴 텍스트는 적절히 잘라서 사용 (토큰 한도 고려)
    max_text_length = 15000  # 약 5000 토큰 정도
    if len(clean_text) > max_text_length:
        clean_text = clean_text[:max_text_length] + "..."

    prompt = f"""
다음 문서를 분석하여 아래 카테고리에 따라 JSON 형식으로 결과를 제공하세요:

1. 문서 구조:
   - paragraph_count: 단락 수
   - sentence_count: 대략적인 문장 수
   - avg_sentence_length: 평균 문장 길이 (단어 수)
   - has_table: 표 포함 여부 (true/false)
   - has_list: 목록 포함 여부 (true/false)
   - has_image: 이미지 태그 포함 여부 (true/false)

2. 어조 분석:
   - formality: 형식성 점수 (0-1, 1이 가장 공식적)
   - sentiment: 감정 점수 (-1: 부정, 0: 중립, 1: 긍정)
   - objectivity: 객관성 점수 (0-1, 1이 가장 객관적)

3. 핵심 키워드:
   - 문서의 핵심 키워드 10개 목록 (중요도 순)

4. 요약:
   - 문서의 핵심 내용을 200자 이내로 요약

응답은 다음 JSON 형식으로 제공하세요:
{{
  "structure": {{
    "paragraph_count": 숫자,
    "sentence_count": 숫자,
    "avg_sentence_length": 숫자,
    "has_table": 불리언,
    "has_list": 불리언,
    "has_image": 불리언
  }},
  "tone": {{
    "formality": 숫자,
    "sentiment": 숫자,
    "objectivity": 숫자
  }},
  "keywords": [키워드1, 키워드2, ...],
  "summary": "요약 내용"
}}

분석할 문서:
```
{clean_text}
```
"""

    try:
        result, token_info = call_openai_api(prompt)
        content = result["content"]

        # JSON 파싱
        try:
            analysis_result = json.loads(content)
            analysis_result["token_info"] = token_info
            return analysis_result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 JSON 부분 추출 시도
            json_pattern = re.compile(r"({.*})", re.DOTALL)
            match = json_pattern.search(content)
            if match:
                try:
                    analysis_result = json.loads(match.group(1))
                    analysis_result["token_info"] = token_info
                    return analysis_result
                except json.JSONDecodeError:
                    logging.error("JSON 추출 실패: 응답 형식이 유효하지 않습니다.")

            # 기본 응답 생성
            logging.warning("JSON 파싱 실패: 기본 응답을 생성합니다.")
            return {
                "structure": {
                    "paragraph_count": 0,
                    "sentence_count": 0,
                    "avg_sentence_length": 0,
                    "has_table": "<table>" in text.lower(),
                    "has_list": "<ul>" in text.lower()
                    or "<ol>" in text.lower()
                    or "<li>" in text.lower(),
                    "has_image": "<img" in text.lower(),
                },
                "tone": {"formality": 0.5, "sentiment": 0, "objectivity": 0.5},
                "keywords": [],
                "summary": "분석 실패",
                "token_info": token_info,
                "raw_response": content,
            }

    except Exception as e:
        logging.error(f"문서 분석 중 오류: {str(e)}")
        return {
            "structure": {
                "paragraph_count": 0,
                "sentence_count": 0,
                "avg_sentence_length": 0,
                "has_table": "<table>" in text.lower(),
                "has_list": "<ul>" in text.lower()
                or "<ol>" in text.lower()
                or "<li>" in text.lower(),
                "has_image": "<img" in text.lower(),
            },
            "tone": {"formality": 0.5, "sentiment": 0, "objectivity": 0.5},
            "keywords": [],
            "summary": "분석 실패",
            "error": str(e),
        }


def _extract_json_from_markdown(text: str) -> Dict:
    """
    마크다운 형식의 텍스트에서 JSON 부분을 추출합니다.

    Args:
        text: 마크다운 텍스트

    Returns:
        추출된 JSON 객체
    """
    # JSON 코드 블록 패턴 (```json과 ``` 사이의 내용)
    json_pattern = r"```(?:json)?\n([\s\S]*?)\n```"
    match = re.search(json_pattern, text)

    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {str(e)}")
            logger.debug(f"파싱 실패한 JSON 문자열: {json_str}")

    # JSON 블록을 찾지 못한 경우, 텍스트 전체가 JSON인지 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.error("JSON 형식을 찾을 수 없음, 빈 사전 반환")
        return {}


def _create_analysis_prompt(template_contents: List[Dict]) -> List[Dict[str, str]]:
    """
    템플릿 분석을 위한 프롬프트를 생성합니다.

    Args:
        template_contents: 분석할 템플릿 내용 목록

    Returns:
        OpenAI API 호출용 메시지 리스트
    """
    # 템플릿 내용을 문자열로 변환
    templates_text = "\n\n===== 템플릿 구분선 =====\n\n".join(
        [
            f"템플릿 ID: {item['id']}\n제목: {item['title']}\n내용:\n{item['content']}"
            for item in template_contents
        ]
    )

    system_message = """
    당신은 문서 템플릿 분석 전문가입니다. 제공된 정부 문서 템플릿을 분석하여 다음 작업을 수행하세요:
    
    1. 각 템플릿의 주요 표준 항목을 식별하고 구조화하세요.
    2. 각 항목에 대한 설명과 예시를 제공하세요.
    3. 좋은 작성 방법에 대한 간략한 조언을 추가하세요.
    4. 템플릿의 핵심 키워드를 추출하세요.
    
    정확히 다음 JSON 형식으로 응답하세요:
    
    ```json
    {
      "templates": [
        {
          "id": "템플릿 ID",
          "title": "템플릿 제목",
          "structure": [
            {
              "name": "항목명",
              "description": "항목 설명",
              "example": "항목 예시",
              "writing_tip": "작성 팁"
            }
          ],
          "keywords": ["키워드1", "키워드2", "..."]
        }
      ]
    }
    ```
    
    항목명은 실제 템플릿에서 사용된 정확한 명칭을 사용하세요.
    """

    user_message = f"""
    다음 문서 템플릿을 분석하세요:
    
    {templates_text}
    
    위 템플릿의 표준 항목을 식별하고 각 항목에 대한 설명, 예시, 작성 팁을 제공하세요.
    형식은 반드시 지정된 JSON 형식으로 응답해주세요.
    """

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def analyze_templates(
    template_contents: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Union[int, float, str]]]:
    """
    여러 문서 템플릿을 분석하여 표준 항목과 내용을 추출합니다.

    Args:
        template_contents: 분석할 템플릿 내용 목록 (각 항목은 id, title, content 키를 포함)

    Returns:
        분석 결과와 토큰 사용량 정보를 포함한 튜플
    """
    try:
        logger.info(f"템플릿 분석 시작: {len(template_contents)}개 템플릿")

        # 분석 프롬프트 생성
        messages = _create_analysis_prompt(template_contents)

        # OpenAI API 호출
        result, token_info = call_openai_api(messages)

        # 응답에서 JSON 추출
        analysis_result = _extract_json_from_markdown(result["content"])

        if not analysis_result:
            logger.warning("템플릿 분석 결과가 비어있거나 유효하지 않음")
            analysis_result = {"templates": [], "error": "분석 결과를 파싱할 수 없음"}

        logger.info(f"템플릿 분석 완료: {len(template_contents)}개 템플릿")
        return analysis_result, token_info

    except Exception as e:
        logger.error(f"템플릿 분석 중 오류 발생: {str(e)}")
        return {"error": f"템플릿 분석 중 오류: {str(e)}"}, {"error": str(e)}


def analyze_templates_from_jsonl(jsonl_file_path: str, output_file_path: str) -> bool:
    """
    JSONL 파일에서 템플릿 데이터를 읽고 분석 결과를 JSON 파일로 저장합니다.

    Args:
        jsonl_file_path: 템플릿 데이터가 저장된 JSONL 파일 경로
        output_file_path: 분석 결과를 저장할 JSON 파일 경로

    Returns:
        bool: 성공 여부
    """
    try:
        # JSONL 파일 읽기
        templates = []
        with open(jsonl_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    templates.append(json.loads(line))

        if not templates:
            logging.error(f"템플릿 데이터가 없습니다: {jsonl_file_path}")
            return False

        # 템플릿 분석
        analysis_results, token_info = analyze_templates(templates)

        # 결과 저장
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)

        logging.info(
            f"템플릿 분석 완료: {len(templates)}개 분석됨, 결과 저장: {output_file_path}"
        )
        return True

    except Exception as e:
        logging.error(f"템플릿 분석 중 오류: {str(e)}")
        return False


def generate_report_prompt(
    user_input: Dict[str, str], selected_templates: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    사용자 입력과 선택된 템플릿을 기반으로 보고서 생성 프롬프트를 구성합니다.

    Args:
        user_input: 사용자가 입력한 보고서 정보 (제목, 목표, 요구사항 등)
        selected_templates: 선택된 템플릿 리스트

    Returns:
        OpenAI API 요청에 사용될 메시지 리스트
    """
    title = user_input.get("title", "제목 없음")
    goal = user_input.get("goal", "")
    requirements = user_input.get("requirements", "")
    audience = user_input.get("audience", "")

    # 템플릿 내용 추출
    template_contents = []

    for template in selected_templates:
        template_content = template.get("content", "")
        template_title = template.get("title", "제목 없음")

        if template_content:
            template_contents.append(f"### {template_title}\n{template_content}")

    # 사용자 요구사항 구성
    user_requirements = []
    if title:
        user_requirements.append(f"제목: {title}")
    if goal:
        user_requirements.append(f"목표: {goal}")
    if requirements:
        user_requirements.append(f"요구사항: {requirements}")
    if audience:
        user_requirements.append(f"대상 독자: {audience}")

    user_requirements_text = "\n".join(user_requirements)
    templates_text = "\n\n".join(template_contents)

    # 최종 프롬프트 구성
    system_message = """당신은 한국의 정부 문서 작성을 돕는 전문가입니다. 사용자가 제공한 템플릿과 요구사항을 기반으로 고품질의 보고서를 작성해주세요.
주어진 템플릿의 구조와 형식을 참고하되, 요구사항에 맞게 내용을 조정하세요.
출력은 마크다운 형식으로 제공하며, 필요에 따라 표와 목록을 포함할 수 있습니다."""

    user_message = f"""## 사용자 요구사항
{user_requirements_text}

## 참고 템플릿
{templates_text}

위 요구사항과 참고 템플릿을 기반으로 보고서를 작성해주세요."""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


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
        # 프롬프트 생성
        messages = generate_report_prompt(user_input, selected_templates)

        # OpenAI API 호출
        result, token_info = call_openai_api(
            messages, model=OPENAI_MODEL, temperature=0.7, max_tokens=2000
        )

        draft_content = result.get("content", "")

        # 응답 형식화
        response = {
            "title": user_input.get("title", "제목 없음"),
            "content": draft_content,
            "timestamp": datetime.now().isoformat(),
        }

        # 토큰 사용량 및 처리 시간 기록
        processing_time = time.time() - start_time
        logger.info(
            f"초안 생성 완료: {processing_time:.2f}초 소요, "
            f"{token_info['total_tokens']}개 토큰 사용"
        )

        return response, token_info

    except Exception as e:
        logger.error(f"초안 생성 중 오류 발생: {str(e)}")
        error_response = {
            "title": user_input.get("title", "제목 없음"),
            "error": f"초안 생성 중 오류: {str(e)}",
            "content": "",
            "timestamp": datetime.now().isoformat(),
        }
        error_token_info = {"error": str(e)}

        return error_response, error_token_info
