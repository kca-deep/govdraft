"""
정부 문서 템플릿 검색 웹 애플리케이션
공공데이터포털 API를 활용하여 정부 문서를 검색하고 결과를 표시합니다.
"""

from flask import Flask
from config import Config
from routes import register_routes
from utils.logging import logger


def create_app(config_class=Config):
    """애플리케이션 팩토리 함수"""
    # Flask 애플리케이션 초기화
    app = Flask(
        __name__,
        template_folder="web",
        static_folder="web/static",
        static_url_path="/static",
    )

    # 라우트 등록
    register_routes(app)

    return app


if __name__ == "__main__":
    # 웹 애플리케이션 실행
    app = create_app()
    port = Config.PORT
    logger.info(f"Flask 웹 애플리케이션을 {port} 포트에서 시작합니다.")
    print(f"Flask 웹 애플리케이션을 http://localhost:{port} 에서 실행 중입니다.")
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=port)
