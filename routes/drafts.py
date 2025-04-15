"""
보고서 생성 라우트 핸들러
AI 보고서 생성 관련 API 엔드포인트를 처리합니다.
"""

import time
import datetime
import os
import json
from flask import Blueprint, request, jsonify, current_app
from routes.main import get_template_cache
from utils.token_utils import calculate_token_cost
from utils.logging import logger
from api.openai_api import (
    analyze_templates as template_analyzer,
    generate_report_prompt,
    call_openai_api,
)
from slugify import slugify

# 블루프린트 생성
drafts_bp = Blueprint("drafts", __name__)

# 결과 파일 저장 경로 설정
RESULT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "result"
)

# 결과 디렉토리가 없으면 생성
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)


@drafts_bp.route("/analyze-templates", methods=["POST"])
def analyze_templates():
    """선택한 템플릿을 분석하여 JSONL 형식으로 저장하는 API"""
    try:
        # 요청 본문 검증
        if not request.is_json:
            logger.error("API 요청이 JSON 형식이 아님")
            return jsonify({"error": "요청은 JSON 형식이어야 합니다."}), 400

        data = request.get_json()

        if not data:
            logger.error("API 요청 본문이 비어 있음")
            return jsonify({"error": "요청 본문이 비어 있습니다."}), 400

        template_ids = data.get("template_ids", [])

        logger.info(f"템플릿 분석 요청: 템플릿 ID={template_ids}")

        # 필수 데이터 검증
        if not template_ids:
            logger.error("템플릿 ID가 제공되지 않음")
            return jsonify({"error": "템플릿 ID가 필요합니다."}), 400

        # 최대 5개 템플릿만 처리
        if len(template_ids) > 5:
            template_ids = template_ids[:5]
            logger.warning(
                f"템플릿 수가 5개를 초과하여 처음 5개만 사용: {template_ids}"
            )

        # 선택된 템플릿 정보 수집
        selected_templates = []
        template_cache = get_template_cache()

        if not template_cache:
            logger.error("템플릿 캐시가 비어 있음")
            return (
                jsonify(
                    {
                        "error": "템플릿 정보를 찾을 수 없습니다. 먼저 검색을 실행해주세요."
                    }
                ),
                404,
            )

        # 캐시된 데이터에서 템플릿 정보 찾기
        for key, data in template_cache.items():
            if "items" in data:
                for item in data["items"]:
                    if item.get("id") in template_ids and item.get("id") not in [
                        t.get("id") for t in selected_templates
                    ]:
                        selected_templates.append(item)

        # 모든 템플릿을 찾았는지 확인
        if len(selected_templates) == len(template_ids):
            logger.info(f"모든 템플릿({len(template_ids)}개)을 캐시에서 찾았습니다.")
        else:
            logger.info(
                f"캐시에서 {len(selected_templates)}개 템플릿을 찾았습니다. (요청: {len(template_ids)}개)"
            )

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

        # 템플릿 데이터 정제 및 JSONL 저장
        jsonl_items = []

        for template in selected_templates:
            # 필요한 필드 추출
            title = template.get("title", "")
            publisher = template.get("publisher", "")
            summary = template.get("summary", "")
            structure = template.get("structure", "")
            content = template.get("content", "")

            # JSONL 형식으로 저장할 데이터 형식 구성
            jsonl_item = {
                "제목": title,
                "발행 부처": publisher,
                "개요": summary,
                "문서 구조": structure,
                "내용": content,
            }

            jsonl_items.append(jsonl_item)

        # 타임스탬프를 이용하여 파일명 생성
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        jsonl_filename = os.path.join(
            RESULT_DIR, f"template_analysis_{timestamp}.jsonl"
        )

        # JSONL 파일 저장
        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for item in jsonl_items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info(
            f"템플릿 분석 완료: 파일={jsonl_filename}, 템플릿 수={len(jsonl_items)}"
        )

        # 응답 생성
        response = {
            "analyzed_at": datetime.datetime.now().isoformat(),
            "template_count": len(jsonl_items),
            "template_ids": template_ids,
            "output_file": jsonl_filename,
            "status": "success",
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"템플릿 분석 중 오류: {str(e)}")
        return jsonify({"error": f"템플릿 분석 중 오류가 발생했습니다: {str(e)}"}), 500


@drafts_bp.route("/analyze-content", methods=["POST"])
def analyze_content():
    """템플릿 내용을 NLP 기법으로 분석하는 API"""
    try:
        # 요청 본문 검증
        if not request.is_json:
            logger.error("API 요청이 JSON 형식이 아님")
            return jsonify({"error": "요청은 JSON 형식이어야 합니다."}), 400

        data = request.get_json()

        if not data:
            logger.error("API 요청 본문이 비어 있음")
            return jsonify({"error": "요청 본문이 비어 있습니다."}), 400

        jsonl_file = data.get("jsonl_file", "")

        logger.info(f"템플릿 내용 분석 요청: JSONL 파일={jsonl_file}")

        # 필수 데이터 검증
        if not jsonl_file:
            logger.error("JSONL 파일 경로가 제공되지 않음")
            return jsonify({"error": "JSONL 파일 경로가 필요합니다."}), 400

        # 파일 존재 확인
        if not os.path.exists(jsonl_file):
            logger.error(f"JSONL 파일을 찾을 수 없음: {jsonl_file}")
            return (
                jsonify({"error": f"JSONL 파일을 찾을 수 없습니다: {jsonl_file}"}),
                404,
            )

        # analysis 디렉토리 확인 및 생성
        analysis_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"
        )
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir)

        # 출력 파일 경로 설정
        filename = os.path.basename(jsonl_file).replace(".jsonl", "")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(
            analysis_dir, f"{filename}_analysis_{timestamp}.json"
        )

        # 템플릿 내용 분석
        success = template_analyzer(jsonl_file, output_file)

        if not success:
            logger.error("템플릿 내용 분석 실패")
            return jsonify({"error": "템플릿 내용 분석에 실패했습니다."}), 500

        # 응답 생성
        response = {
            "analyzed_at": datetime.datetime.now().isoformat(),
            "jsonl_file": jsonl_file,
            "output_file": output_file,
            "status": "success",
        }

        logger.info(f"템플릿 내용 분석 완료: 결과 파일={output_file}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"템플릿 내용 분석 중 오류: {str(e)}")
        return (
            jsonify({"error": f"템플릿 내용 분석 중 오류가 발생했습니다: {str(e)}"}),
            500,
        )


@drafts_bp.route("/generate", methods=["POST"])
def generate_draft():
    """선택한 템플릿을 기반으로 AI 보고서 생성 API"""
    try:
        # 요청 본문 검증
        if not request.is_json:
            logger.error("API 요청이 JSON 형식이 아님")
            return jsonify({"error": "요청은 JSON 형식이어야 합니다."}), 400

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
        template_cache = get_template_cache()

        if not template_cache:
            logger.error("템플릿 캐시가 비어 있음")
            return (
                jsonify(
                    {
                        "error": "템플릿 정보를 찾을 수 없습니다. 먼저 검색을 실행해주세요."
                    }
                ),
                404,
            )

        # 캐시된 데이터에서 템플릿 정보 찾기
        for key, data in template_cache.items():
            if "items" in data:
                for item in data["items"]:
                    if item.get("id") in template_ids and item.get("id") not in [
                        t.get("id") for t in selected_templates
                    ]:
                        selected_templates.append(item)

        # 모든 템플릿을 찾았는지 확인
        if len(selected_templates) == len(template_ids):
            logger.info(f"모든 템플릿({len(template_ids)}개)을 캐시에서 찾았습니다.")
        else:
            logger.info(
                f"캐시에서 {len(selected_templates)}개 템플릿을 찾았습니다. (요청: {len(template_ids)}개)"
            )

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

        # 보고서 생성용 프롬프트 구성
        prompt = generate_report_prompt(user_input, selected_templates)

        # OpenAI API 호출하여 보고서 생성
        start_time = time.time()
        response = call_openai_api(prompt)
        end_time = time.time()

        # API 응답에서 내용 추출
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # 토큰 사용량 및 비용 계산
        input_tokens = response.get("usage", {}).get("prompt_tokens", 0)
        output_tokens = response.get("usage", {}).get("completion_tokens", 0)
        token_cost = calculate_token_cost(input_tokens, output_tokens)

        # 응답 구성
        result = {
            "content": content,
            "token_info": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": token_cost["cost_usd"],
                "cost_krw": token_cost["cost_krw"],
                "processing_time": end_time - start_time,
            },
        }

        # 결과 저장 (옵션)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"generated_report_{timestamp}.json"
        result_path = os.path.join("results", result_filename)

        # results 디렉터리가 없으면 생성
        os.makedirs("results", exist_ok=True)

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return jsonify(
            {"result": "success", "report": result, "resultFile": result_filename}
        )

    except Exception as e:
        logger.error(f"보고서 생성 중 오류: {str(e)}")
        return jsonify({"error": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"}), 500


@drafts_bp.route("/api/analyze", methods=["POST"])
def api_analyze_templates():
    """
    선택된 템플릿들을 분석하여 공통 키워드, 형식성, 객관성 등을 파악
    """
    try:
        # POST 요청 데이터 파싱
        data = request.get_json()
        if not data or "templates" not in data:
            logger.warning("템플릿 데이터 없이 /api/analyze 요청 발생")
            return jsonify({"error": "템플릿 데이터가 필요합니다"}), 400

        templates = data.get("templates", [])
        if not templates:
            logger.warning("빈 템플릿 목록으로 /api/analyze 요청 발생")
            return jsonify({"error": "최소 하나 이상의 템플릿이 필요합니다"}), 400

        logger.info(f"/api/analyze 요청 시작: {len(templates)}개 템플릿")
        start_time = time.time()

        # 템플릿 분석 수행
        analysis_result = template_analyzer(templates)

        # 결과 저장
        results_dir = os.path.join(current_app.root_path, "results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        result_file = os.path.join(results_dir, f"analysis_{timestamp}.json")

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)

        # 처리 시간 측정 및 로깅
        processing_time = time.time() - start_time
        logger.info(
            f"/api/analyze 요청 완료: {processing_time:.2f}초 소요, 결과 저장: {result_file}"
        )

        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"/api/analyze 처리 중 오류: {str(e)}")
        return jsonify({"error": f"템플릿 분석 중 오류가 발생했습니다: {str(e)}"}), 500


@drafts_bp.route("/api/generate", methods=["POST"])
def api_generate_report():
    """
    사용자 입력과 선택된 템플릿을 기반으로 보고서 생성
    """
    try:
        # POST 요청 데이터 파싱
        data = request.get_json()
        if not data:
            logger.warning("데이터 없이 /api/generate 요청 발생")
            return jsonify({"error": "보고서 생성에 필요한 데이터가 없습니다"}), 400

        user_input = data.get("userInput", {})
        templates = data.get("templates", [])

        if not user_input:
            logger.warning("사용자 입력 없이 /api/generate 요청 발생")
            return jsonify({"error": "보고서 제목과 요구사항이 필요합니다"}), 400

        if not templates:
            logger.warning("템플릿 없이 /api/generate 요청 발생")
            return jsonify({"error": "최소 하나 이상의 템플릿이 필요합니다"}), 400

        title = user_input.get("title", "제목 없음")
        logger.info(
            f"/api/generate 요청 시작: 제목='{title}', {len(templates)}개 템플릿"
        )
        start_time = time.time()

        # 보고서 생성 프롬프트 구성
        prompt = generate_report_prompt(user_input, templates)

        # OpenAI API 호출
        response = call_openai_api(prompt)

        # 응답에서 생성된 보고서 추출
        generated_content = (
            response.get("choices", [{}])[0].get("message", {}).get("content", "")
        )

        # 토큰 사용량 및 비용 계산
        token_usage = response.get("usage", {})
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)

        # 비용 계산
        cost_info = calculate_token_cost(input_tokens, output_tokens)

        # 결과 저장
        results_dir = os.path.join(current_app.root_path, "results")
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        title_slug = slugify(title)
        result_file = os.path.join(results_dir, f"report_{title_slug}_{timestamp}.json")

        result = {
            "title": title,
            "content": generated_content,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "cost": cost_info,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "user_input": user_input,
                "num_templates_used": len(templates),
            },
        }

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 처리 시간 측정 및 로깅
        processing_time = time.time() - start_time
        logger.info(
            f"/api/generate 요청 완료: {processing_time:.2f}초 소요, {input_tokens + output_tokens}개 토큰 사용, 결과 저장: {result_file}"
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"/api/generate 처리 중 오류: {str(e)}")
        return jsonify({"error": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"}), 500
