import datetime
# import logging

from flask import Blueprint, request, render_template, current_app

# メール
from ...email import send_email

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti, set_refresh_cookies

# DB関連
from apps.api.auth.models import User

api = Blueprint(
    "api",
    __name__
)

# api.logger.setLevel(logging.DEBUG)

@api.route("/", methods=["GET", "POST"])
def index():
    current_app.logger.warning(f"【warning!!!!!】不正なアクセスが行われようとした形跡があります")
    
    if request.method == "POST":
        email = request.form["email"]

        # # メール送信テスト（デバッグ用）
        send_email(email,"test","/test_mail",admin_name="名無しの専門学生")
        # #


        ############# ここで2要素認証としてメールを送信する

        return f"Hello, {email}!"
    else:
        return "Hello, Guest!"

@api.route("/login", methods=["POST"])
def login():
    current_app.logger.info("login-APIにアクセスがありました")
    """
    request.body(json)
    {
        "email": "...",
        "password": "..."
    }
    """
    try:
        login_data = request.get_json()
        email = login_data.get("email")
        password = login_data.get("password")

        user = User.query.filter_by(email=email).first()
        print(login_data)
    except Exception as e:
        print(e)

