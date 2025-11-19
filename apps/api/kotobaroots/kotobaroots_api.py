from flask import Blueprint, request, render_template, current_app, jsonify

from ...email import send_email

from flask_jwt_extended import jwt_required, get_jwt_identity

### DB
from apps.extensions import db

from apps.api.auth.models import User
from apps.api.kotobaroots.models import Contact,LearningConfig,Language

### マイフレーズ（マッピング）
from apps.api.kotobaroots.utils import get_myphrase_model


api = Blueprint(
    "kotobaroots",
    __name__
)

@api.route("/")
def index():
    current_app.logger.warning(f"【warning!!!!!】不正なアクセスが行われようとした形跡があります")

### 問い合わせ
@api.route("/contact", methods=["POST"])
@jwt_required()
def contact():
    current_app.logger.info("contact-APIにアクセスがありました")
    """
    request.body(json)
    {
        "content": "..."
    }
    """
    try:
        contact_data = request.get_json()
        # user_email = contact_data.get("user_email")
        current_user_id=get_jwt_identity()
        content = contact_data.get("content")

        user = User.query.filter_by(id=current_user_id).first()

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

# ### ウェルカムページ（言語選択）
# @api.route("/welcome")


### マイフレーズ
@api.route("/myphrase", methods=["GET"])
@jwt_required()
def myphrase():
    current_app.logger.info("myphrase-APIにアクセスがありました")
    """
    request.body(json)
    {
    
    }
    """
    # req_data = request.get_json()
    # email = req_data.get("email")
    current_user_id=get_jwt_identity()

    # user = User.query.filter_by(email=email).first()

    # 現在適用中のlearning_configを取得
    active_learning_config = LearningConfig.query.join(User).join(Language).filter(User.id == current_user_id).filter(LearningConfig.is_applying == True).first()

    if not active_learning_config:
        current_app.logger.error(f"学習設定が適切に設定されていません\nuser_id : {current_user_id}")
        ########## 現状500番で返しているが、本番時には学習設定を必ずしてもらう画面に遷移するために他のステータスコードを返す
        return jsonify({"msg": "学習設定が適切に設定されていません"}), 500

    language = active_learning_config.language.language
    ## もし対応言語を増やす場合は必ずモデルから定義すること！！！
    TargetModel = get_myphrase_model(language)

    if not TargetModel:
        current_app.logger.error(f"対応する言語モデルが見つかりません: {language}")
        return jsonify({"msg": "対応していない言語です。"}), 400
    
    current_user_myphrases = TargetModel.query.filter_by(user_id=current_user_id).all()

    response_list = []
    for item in current_user_myphrases:
        response_list.append({
            "id": item.id,
            "phrase": item.phrase,
            "mean": item.mean
        })

    return jsonify(response_list), 200

### プロフィール
@api.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    """
    request.body(json)
    {
    
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "ユーザーが見つかりません"}), 404
 
        profile_data = {
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
 
        return jsonify(profile_data), 200
 
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500