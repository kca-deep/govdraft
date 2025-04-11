"""
회원 관리 패키지
사용자 인증 및 계정 관리 기능을 제공합니다.
"""

from config import db
from routes.member.models import init_user_model

# User 모델 초기화
User = init_user_model(db)
