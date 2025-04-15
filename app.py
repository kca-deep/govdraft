"""
정부 문서 템플릿 검색 웹 애플리케이션
공공데이터포털 API를 활용하여 정부 문서를 검색하고 결과를 표시합니다.
"""

from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from config import Config, db
from routes import register_routes
from utils.logging import logger
from routes.main import (
    format_date_filter,
    format_content_filter,
    get_meta_fields,
)  # 필터 및 헬퍼 함수 임포트
from routes.member import User
import os


def create_app(config_class=Config):
    """애플리케이션 팩토리 함수"""
    # Flask 애플리케이션 초기화
    app = Flask(
        __name__,
        template_folder="web",
        static_folder="web/static",
        static_url_path="/static",
    )

    # 설정 적용
    app.config.from_object(config_class)

    # CORS 설정
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 데이터베이스 초기화
    db.init_app(app)

    # Flask-Login 설정
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "member.login"
    login_manager.login_message = "이 페이지에 접근하려면 로그인이 필요합니다."

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 라우트 등록
    register_routes(app)

    # Jinja 환경에 필터 및 헬퍼 함수 등록
    app.jinja_env.filters["format_date"] = format_date_filter
    app.jinja_env.filters["format_content"] = format_content_filter
    app.jinja_env.globals["get_meta_fields"] = get_meta_fields
    logger.info("Jinja 필터 및 헬퍼 함수 등록 완료")

    # 데이터베이스 생성
    with app.app_context():
        db.create_all()
        logger.info("데이터베이스 테이블 생성 완료")

    return app


if __name__ == "__main__":
    # 웹 애플리케이션 실행
    app = create_app()
    port = Config.PORT
    logger.info(f"Flask 웹 애플리케이션을 {port} 포트에서 시작합니다.")
    print(f"Flask 웹 애플리케이션을 http://localhost:{port} 에서 실행 중입니다.")
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=port)
