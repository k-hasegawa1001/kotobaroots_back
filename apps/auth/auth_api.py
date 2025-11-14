from flask import Blueprint, request, render_template

from ..email import send_email


api = Blueprint(
    "api",
    __name__
)

@api.route("/", methods=["GET", "POST"])
def authentication_at_email_address():
    if request.method == "POST":
        email = request.form["email"]

        # メール送信テスト（デバッグ用）
        send_email(email,"test","test_mail",admin_name="名無しの専門学生")
        #

        return f"Hello, {email}!"
    else:
        return "Hello, Guest!"



