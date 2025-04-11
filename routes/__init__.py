"""
라우트 핸들러 패키지
"""

from routes.main import main_bp
from routes.drafts import drafts_bp


def register_routes(app):
    """모든 블루프린트를 Flask 앱에 등록합니다."""
    app.register_blueprint(main_bp)
    app.register_blueprint(drafts_bp, url_prefix="/api/drafts")
