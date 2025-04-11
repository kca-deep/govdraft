"""
회원 관리 폼 정의
회원가입, 로그인 등의 폼을 정의합니다.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from routes.member import User


class LoginForm(FlaskForm):
    """로그인 폼"""

    username = StringField("아이디", validators=[DataRequired()])
    password = PasswordField("비밀번호", validators=[DataRequired()])
    remember_me = BooleanField("로그인 상태 유지")
    submit = SubmitField("로그인")


class RegistrationForm(FlaskForm):
    """회원가입 폼"""

    username = StringField(
        "아이디",
        validators=[
            DataRequired(),
            Length(min=3, max=50, message="아이디는 3자 이상 50자 이하여야 합니다."),
        ],
    )
    email = StringField(
        "이메일",
        validators=[
            DataRequired(),
            Email(message="유효한 이메일 주소를 입력해주세요."),
        ],
    )
    full_name = StringField(
        "이름",
        validators=[
            DataRequired(),
            Length(min=2, max=100, message="이름은 2자 이상 100자 이하여야 합니다."),
        ],
    )
    password = PasswordField(
        "비밀번호",
        validators=[
            DataRequired(),
            Length(min=8, message="비밀번호는 최소 8자 이상이어야 합니다."),
        ],
    )
    password2 = PasswordField(
        "비밀번호 확인",
        validators=[
            DataRequired(),
            EqualTo("password", message="비밀번호가 일치하지 않습니다."),
        ],
    )
    submit = SubmitField("회원가입")

    def validate_username(self, username):
        """아이디 중복 검사"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(
                "이미 사용 중인 아이디입니다. 다른 아이디를 선택해주세요."
            )

    def validate_email(self, email):
        """이메일 중복 검사"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("이미 등록된 이메일 주소입니다.")


class PasswordChangeForm(FlaskForm):
    """비밀번호 변경 폼"""

    current_password = PasswordField(
        "현재 비밀번호",
        validators=[DataRequired(message="현재 비밀번호를 입력해주세요.")],
    )

    new_password = PasswordField(
        "새 비밀번호",
        validators=[
            DataRequired(message="새 비밀번호를 입력해주세요."),
            Length(min=8, message="비밀번호는 최소 8자 이상이어야 합니다."),
        ],
    )

    confirm_password = PasswordField(
        "새 비밀번호 확인",
        validators=[
            DataRequired(message="비밀번호 확인을 입력해주세요."),
            EqualTo("new_password", message="비밀번호가 일치하지 않습니다."),
        ],
    )

    submit = SubmitField("비밀번호 변경")
