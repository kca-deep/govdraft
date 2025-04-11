"""
회원 관리 라우트 핸들러
로그인, 로그아웃, 회원가입 등의 인증 관련 라우트를 처리합니다.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse  # 대신 werkzeug.urls.url_parse 대체
from config import db
from routes.member import User
from routes.member.forms import LoginForm, RegistrationForm, PasswordChangeForm
from utils.logging import logger
from datetime import datetime

# 블루프린트 생성
member_bp = Blueprint("member", __name__)


@member_bp.route("/login", methods=["GET", "POST"])
def login():
    """로그인 페이지"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("아이디 또는 비밀번호가 올바르지 않습니다.", "error")
            logger.warning(f"로그인 실패: {form.username.data}")
            return redirect(url_for("member.login"))

        if not user.is_active:
            flash("비활성화된 계정입니다. 관리자에게 문의하세요.", "error")
            logger.warning(f"비활성화된 계정 로그인 시도: {user.username}")
            return redirect(url_for("member.login"))

        login_user(user, remember=form.remember_me.data)
        user.update_last_login()
        logger.info(f"로그인 성공: {user.username}")

        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("main.index")

        return redirect(next_page)

    return render_template("member/login.html", title="로그인", form=form)


@member_bp.route("/logout")
def logout():
    """로그아웃"""
    if current_user.is_authenticated:
        logger.info(f"로그아웃: {current_user.username}")
    logout_user()
    return redirect(url_for("main.index"))


@member_bp.route("/register", methods=["GET", "POST"])
def register():
    """회원가입 페이지"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        logger.info(f"신규 회원가입: {user.username}, {user.email}")
        flash("회원가입이 완료되었습니다. 이제 로그인할 수 있습니다.", "success")
        return redirect(url_for("member.login"))

    return render_template("member/register.html", title="회원가입", form=form)


@member_bp.route("/profile")
@login_required
def profile():
    """사용자 프로필 페이지"""
    return render_template("member/profile.html", title="내 프로필")


@member_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """비밀번호 변경 페이지"""
    form = PasswordChangeForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("현재 비밀번호가 올바르지 않습니다.", "error")
            return redirect(url_for("member.change_password"))

        current_user.set_password(form.new_password.data)
        db.session.commit()
        logger.info(f"비밀번호 변경: {current_user.username}")
        flash("비밀번호가 성공적으로 변경되었습니다.", "success")
        return redirect(url_for("member.profile"))

    return render_template(
        "member/change_password.html", title="비밀번호 변경", form=form
    )


@member_bp.route("/deactivate", methods=["POST"])
@login_required
def deactivate_account():
    """계정 비활성화"""
    # 추가 보안을 위해 확인 과정을 거칠 수 있습니다
    username = current_user.username
    current_user.deactivate_account()
    logout_user()

    logger.info(f"계정 비활성화: {username}")
    flash(
        "계정이 비활성화되었습니다. 필요할 때 관리자에게 문의하여 재활성화할 수 있습니다.",
        "info",
    )
    return redirect(url_for("main.index"))
