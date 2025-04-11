"""
메인 라우트 핸들러
기본 페이지, 검색, 토큰 계산 및 오류 페이지 라우트를 처리합니다.
"""

import datetime
from flask import Blueprint, render_template, request, jsonify
from api.government_api import fetch_government_templates
from utils.token_utils import calculate_token_cost
from utils.logging import logger

# 블루프린트 생성
main_bp = Blueprint("main", __name__)

# 캐시를 활용한 API 응답 저장
template_cache = {}


# 기본 페이지 관련 라우트
@main_bp.route("/")
def index():
    """메인 페이지"""
    return render_template("index.html")


@main_bp.route("/health")
def health_check():
    """서버 상태 확인용 엔드포인트"""
    return jsonify({"status": "ok", "timestamp": datetime.datetime.now().isoformat()})


# 검색 관련 라우트
@main_bp.route("/search", methods=["GET"])
def search_templates():
    """템플릿 검색 API"""
    keyword = request.args.get("keyword", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    doc_type = request.args.get("doc_type", "press")
    manager = request.args.get("manager", "")
    use_cache = request.args.get("use_cache", "true").lower() == "true"

    logger.info(
        f"템플릿 검색 요청: 키워드='{keyword}', 페이지={page}, 페이지당 결과수={per_page}, "
        f"문서유형={doc_type}, 담당자='{manager}'"
    )

    # 캐시 키 생성
    cache_key = f"{keyword}:{page}:{per_page}:{doc_type}:{manager}"

    # 캐시된 결과가 있고 캐시 사용이 활성화된 경우 캐시에서 반환
    if use_cache and cache_key in template_cache:
        logger.info(f"캐시된 결과 반환: {cache_key}")
        return jsonify(template_cache[cache_key])

    # API 호출
    result = fetch_government_templates(keyword, page, per_page, doc_type, manager)

    # 결과 캐싱 (오류가 없는 경우에만)
    if "error" not in result and use_cache:
        template_cache[cache_key] = result

    return jsonify(result)


# 토큰 계산 관련 라우트
@main_bp.route("/api/token-cost", methods=["POST"])
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


# 에러 핸들링 라우트
@main_bp.errorhandler(404)
def page_not_found(e):
    """404 에러 처리"""
    return render_template("404.html"), 404


@main_bp.errorhandler(500)
def internal_server_error(e):
    """500 에러 처리"""
    logger.error(f"서버 오류: {str(e)}")
    return render_template("500.html"), 500


# 캐시 가져오기 함수 (drafts.py에서 사용)
def get_template_cache():
    return template_cache
