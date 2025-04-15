"""
메인 라우트 핸들러
기본 페이지, 검색, 토큰 계산 및 오류 페이지 라우트를 처리합니다.
"""

import datetime
from flask import Blueprint, render_template, request, jsonify, abort
from markupsafe import Markup  # Markup 임포트
import re  # 정규표현식 임포트
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
@main_bp.route("/api/search", methods=["GET"])
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


# 템플릿 상세 정보 관련 헬퍼 함수 및 필터
def get_meta_fields(doc_type):
    """문서 유형에 따른 메타 필드 구성 반환"""
    meta_fields_config = {
        "보도자료": [
            {"label": "발행 부처", "key": "ministry"},
            {"label": "발행 부서", "key": "department"},
            {"label": "담당자", "key": "manager"},
            {"label": "보도일자", "key": "date", "isDate": True},
            {"label": "보도시점", "key": "time"},
        ],
        "연설문": [
            {"label": "연설자", "key": "person"},
            {"label": "연설 장소", "key": "place"},
            {"label": "연설일", "key": "date", "isDate": True},
        ],
        "발간사": [
            {"label": "작성자", "key": "person"},
            {"label": "발간일", "key": "date", "isDate": True},
        ],
        "정책보고서": [
            {"label": "발행 부처", "key": "ministry"},
            {"label": "발행 부서", "key": "department"},
            {"label": "담당자", "key": "manager"},
            {"label": "작성일", "key": "date", "isDate": True},
        ],
        "회의": [
            {"label": "일자", "key": "date", "isDate": True},
            {"label": "장소", "key": "place"},
            {"label": "참석자", "key": "person"},
        ],
        "행사계획": [
            {"label": "일자", "key": "date", "isDate": True},
            {"label": "장소", "key": "place"},
            {"label": "참석자", "key": "person"},
        ],
        "default": [
            {"label": "문서 유형", "key": "docType"},
            {"label": "날짜", "key": "date", "isDate": True},
            {"label": "문서 ID", "key": "id"},
        ],
    }
    # doc_type 문자열에 키워드가 포함되어 있는지 확인하여 반환
    for type_keyword, fields in meta_fields_config.items():
        if type_keyword in (doc_type or ""):
            return fields
    return meta_fields_config["default"]


def format_date_filter(value):
    """날짜 문자열을 YYYY-MM-DD 형식으로 변환"""
    if not value:
        return ""
    try:
        # 다양한 날짜 형식 시도 (예: 'YYYYMMDD', 'YYYY-MM-DD', 'YYYY.MM.DD')
        dt_obj = None
        if isinstance(value, str):
            if re.match(r"^\d{8}$", value):
                dt_obj = datetime.datetime.strptime(value, "%Y%m%d")
            elif re.match(r"^\d{4}-\d{2}-\d{2}", value):
                dt_obj = datetime.datetime.fromisoformat(
                    value.split("T")[0]
                )  # ISO 형식 처리
            elif re.match(r"^\d{4}\.\d{2}\.\d{2}", value):
                dt_obj = datetime.datetime.strptime(
                    value.split(".")[0]
                    + "."
                    + value.split(".")[1]
                    + "."
                    + value.split(".")[2],
                    "%Y.%m.%d",
                )

        if dt_obj:
            return dt_obj.strftime("%Y-%m-%d")
        # datetime 객체인 경우
        elif isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d")
        # 변환 실패 시 원본 반환 (또는 오류 처리)
        return str(value)
    except ValueError:
        return str(value)  # 파싱 실패 시 원본 값 반환


def format_content_filter(content):
    """텍스트 내용의 줄바꿈을 HTML 태그로 변환"""
    if not content:
        return ""
    # HTML 태그가 이미 있는지 간단히 확인
    if "<" in content and ">" in content:
        # 이미 HTML이면 그대로 반환 (더 정교한 확인 필요 시 라이브러리 사용)
        # 간단한 빈 <p> 태그 제거
        content = re.sub(r"<p>\s*</p>", "", content, flags=re.IGNORECASE)
        return Markup(content)
    else:
        # 일반 텍스트면 줄바꿈 처리
        lines = content.split("\n")
        formatted_lines = [
            f"<p>{line}</p>" if line.strip() else "<br>" for line in lines
        ]
        return Markup("".join(formatted_lines))


# Jinja 환경에 필터 등록 (앱 초기화 시 수행 필요)
# main_bp.add_app_template_filter(format_date_filter, 'format_date')
# main_bp.add_app_template_filter(format_content_filter, 'format_content')
# main_bp.add_app_template_global(get_meta_fields, 'get_meta_fields') # 헬퍼 함수 등록


@main_bp.route("/template_detail/<template_id>")
def template_detail(template_id):
    """템플릿 상세 정보 HTML 조각 반환"""
    logger.info(f"템플릿 상세 정보 요청: ID={template_id}")

    # 캐시에서 템플릿 찾기 시도
    found_template = None
    for cache_key, cached_data in template_cache.items():
        if isinstance(cached_data, dict) and "items" in cached_data:
            for item in cached_data["items"]:
                # API 응답 형식에 따라 id 필드 접근 방식 조정 필요
                # 예: item['id'], item.get('id') 등
                item_id = item.get("id") or item.get(
                    "_id"
                )  # 다양한 ID 필드 가능성 고려
                if str(item_id) == str(template_id):
                    found_template = item
                    break
        if found_template:
            break

    if not found_template:
        # 캐시에 없으면 API를 통해 가져오기 시도 (단일 항목 조회 API가 있다면 사용)
        # 여기서는 예시로 검색 API를 활용 (비효율적일 수 있음)
        logger.warning(f"템플릿 ID {template_id}가 캐시에 없어 API 재검색 시도")
        # 단일 ID 검색 기능이 API에 없다고 가정하고, 키워드 없이 전체 검색 후 필터링
        # 실제로는 ID 기반 조회 API 사용 권장
        result = fetch_government_templates(
            keyword=template_id, page=1, per_page=1, doc_type="all", manager="%"
        )  # ID로 검색 시도
        if result.get("items") and str(result["items"][0].get("id")) == str(
            template_id
        ):
            found_template = result["items"][0]
        else:
            # 그래도 없으면 404
            logger.error(f"템플릿 ID {template_id}를 찾을 수 없음")
            abort(404, description="Template not found")

    # 템플릿 데이터와 헬퍼 함수를 컨텍스트로 전달하여 렌더링
    return render_template(
        "template_detail.html", template=found_template, get_meta_fields=get_meta_fields
    )


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
