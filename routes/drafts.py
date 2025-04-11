"""
보고서 생성 라우트 핸들러
AI 보고서 생성 관련 API 엔드포인트를 처리합니다.
"""

import time
import datetime
from flask import Blueprint, request, jsonify
from routes.main import get_template_cache
from utils.token_utils import calculate_token_cost
from utils.logging import logger

# 블루프린트 생성
drafts_bp = Blueprint("drafts", __name__)


@drafts_bp.route("/generate", methods=["POST"])
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
        template_cache = get_template_cache()

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
