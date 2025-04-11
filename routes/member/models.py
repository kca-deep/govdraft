"""
회원 관리 관련 데이터베이스 모델
사용자 계정 모델을 정의합니다.
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# SQLAlchemy 객체는 외부에서 주입됩니다. (from config import db)
db = None


def init_user_model(sqlalchemy_db):
    """User 모델 클래스를 초기화하고 반환합니다."""
    global db
    db = sqlalchemy_db

    class User(db.Model, UserMixin):
        """사용자 계정 모델"""

        __tablename__ = "users"

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), unique=True, nullable=False)
        email = db.Column(db.String(100), unique=True, nullable=False)
        full_name = db.Column(db.String(100), nullable=False)
        password_hash = db.Column(db.String(256), nullable=False)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_login = db.Column(db.DateTime, nullable=True)

        def set_password(self, password):
            """비밀번호를 해시하여 저장"""
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            """비밀번호 검증"""
            return check_password_hash(self.password_hash, password)

        def update_last_login(self):
            """마지막 로그인 시간 업데이트"""
            self.last_login = datetime.utcnow()
            db.session.commit()

        def activate_account(self):
            """계정 활성화"""
            self.is_active = True
            db.session.commit()

        def deactivate_account(self):
            """계정 비활성화"""
            self.is_active = False
            db.session.commit()

        def __repr__(self):
            return f"<User {self.username}>"

    return User
