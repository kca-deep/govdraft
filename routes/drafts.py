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
    analyze_templates_from_json,  # 함수 이름 변경
    generate_report_prompt,
    call_openai_api,
    generate_draft as generate_draft_api,
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
        json_filename = os.path.join(
            RESULT_DIR, f"template_analysis_{timestamp}.json"  # 확장자 변경
        )

        # JSON 파일 저장
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(
                jsonl_items, f, ensure_ascii=False, indent=2
            )  # json.dump 사용 및 들여쓰기 추가

        logger.info(
            f"템플릿 분석 완료: 파일={json_filename}, 템플릿 수={len(jsonl_items)}"  # 로그 메시지 파일명 변수 변경
        )

        # 응답 생성
        response = {
            "analyzed_at": datetime.datetime.now().isoformat(),
            "template_count": len(jsonl_items),
            "template_ids": template_ids,
            "output_file": json_filename,  # 응답의 파일명 변수 변경
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

        # 타임스탬프를 이용하여 파일명 생성
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"template_analysis_{timestamp}.json"
        output_file = os.path.join(analysis_dir, output_filename)

        # 템플릿 내용 분석 (수정된 함수 호출)
        success = analyze_templates_from_json(jsonl_file, output_file)

        if not success:
            logger.error("템플릿 내용 분석 실패")
            return jsonify({"error": "템플릿 내용 분석에 실패했습니다."}), 500

        # 응답 생성 - 파일 이름만 반환하여 경로 문제 방지
        response = {
            "analyzed_at": datetime.datetime.now().isoformat(),
            "jsonl_file": jsonl_file,
            "output_file": output_filename,  # 파일 이름만 반환 (경로 제외)
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

        # 사용자 입력 데이터 형식화
        user_input_dict = {"title": user_input}

        # api/openai_api.py에 있는 generate_draft 함수 호출
        result, token_info = generate_draft_api(user_input_dict, selected_templates)

        # 응답 구성
        response = {
            "result": "success",
            "report": result,
            "token_info": token_info,
            "resultFile": f"generated_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        }

        # analysis 디렉토리 확인 및 생성
        analysis_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"
        )
        if not os.path.exists(analysis_dir):
            os.makedirs(analysis_dir)

        # 결과 저장
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"generated_report_{timestamp}.json"
        result_path = os.path.join(analysis_dir, result_filename)

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 파일 크기 계산 (KB)
        file_size_kb = round(os.path.getsize(result_path) / 1024, 2)

        # 응답 업데이트 - 파일명만 포함하고 파일 크기 추가
        response["resultFile"] = result_filename
        response["size_kb"] = file_size_kb

        return jsonify(response)

    except Exception as e:
        logger.error(f"보고서 생성 중 오류: {str(e)}")
        return jsonify({"error": f"보고서 생성 중 오류가 발생했습니다: {str(e)}"}), 500


# 분석 결과 파일 서빙 라우트 추가
@drafts_bp.route("/analysis/<filename>")
def serve_analysis_file(filename):
    """분석 결과 파일을 제공하는 API"""
    try:
        # analysis 디렉토리 경로
        analysis_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "analysis"
        )

        # 파일 경로 구성
        file_path = os.path.join(analysis_dir, filename)

        # 파일 존재 확인
        if not os.path.exists(file_path):
            logger.error(f"분석 파일을 찾을 수 없음: {filename}")
            return jsonify({"error": f"파일을 찾을 수 없습니다: {filename}"}), 404

        # 파일 내용 읽기
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        return jsonify(file_content)

    except Exception as e:
        logger.error(f"분석 파일 제공 중 오류: {str(e)}")
        return (
            jsonify({"error": f"분석 파일 제공 중 오류가 발생했습니다: {str(e)}"}),
            500,
        )
