from flask import Blueprint, request, render_template, current_app, jsonify

from ...email import send_email

### DB
from apps.extensions import db

from apps.api.auth.models import User
from apps.api.kotobaroots.models import Contact


api = Blueprint(
    "kotobaroots",
    __name__
)

@api.route("/")
def index():
    current_app.logger.warning(f"【warning!!!!!】不正なアクセスが行われようとした形跡があります")

### 問い合わせ
@api.route("/contact", methods=["POST"])
def contact():
    current_app.logger.info("contact-APIにアクセスがありました")
    """
    request.body(json)
    {
        "user_email": "...",
        "content": "..."
    }
    """
    try:
        contact_data = request.json()
        user_email = contact_data.get("user_email")
        content = contact_data.get("content")

        user = User.query.filter_by(email=user_email).first()

        new_contact = Contact(user_id=user.id, content=content)

        db.session.add(new_contact)
        db.session.commit()

        response_body={
            "msg": "お問い合わせが送信されました！"
        }

        response = jsonify(response_body)

        return response, 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

### マイフレーズ
@api.route("/myphrase", methods=["GET"])
def myphrase():
    current_app.logger.info("myphrase-APIにアクセスがありました")
    """
    request.body(json)
    {
        "email": "..."
    }
    """
    req_data = request.get_json()
    email = req_data.get("email")

    user = User.query.filter_by(email=email).first()
