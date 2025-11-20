from flask import Blueprint, request, render_template, current_app, jsonify

from ...email import send_email

from flask_jwt_extended import jwt_required, get_jwt_identity

### DB
from sqlalchemy import delete
from sqlalchemy.sql.expression import func

from apps.extensions import db

from apps.api.auth.models import User
from apps.api.kotobaroots.models import Contact,LearningConfig,Language

### マイフレーズ（マッピング）
from apps.api.kotobaroots.utils import get_myphrase_model

MAX_MYPHRASE_COUNT = 100


api = Blueprint(
    "kotobaroots",
    __name__
)

@api.route("/")
def index():
    current_app.logger.warning(f"【warning!!!!!】不正なアクセスが行われようとした形跡があります")

### 問い合わせ（長谷川）
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
## トップ（長谷川）
@api.route("/myphrase", methods=["GET"])
@jwt_required()
def myphrase():
    current_app.logger.info("myphrase-APIにアクセスがありました")
    """
    request.body(json)
    {
    
    }
    """
    try:
        # req_data = request.get_json()
        # email = req_data.get("email")
        current_user_id=get_jwt_identity()

        # user = User.query.filter_by(email=email).first()

        # 現在適用中のlearning_configを取得
        active_learning_config = LearningConfig.query \
            .join(User) \
            .join(Language) \
            .filter(User.id == current_user_id) \
            .filter(LearningConfig.is_applying == True) \
            .first()
        
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
        
        current_user_myphrases = TargetModel.query \
            .filter_by(user_id=current_user_id) \
            .all()

        response_list = []
        for item in current_user_myphrases:
            response_list.append({
                "id": item.id,
                "phrase": item.phrase,
                "mean": item.mean
            })

        res_body = {
            "myphrases": response_list,
            "question_num": active_learning_config.myphrase_question_num
        }

        return jsonify(res_body), 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

## マイフレーズ追加（長谷川）
@api.route("/myphrase", methods=["POST"])
@jwt_required()
def myphrase_add():
    current_app.logger.info("myphrase_add-APIにアクセスがありました")
    """
    {
        "phrases": "...",
        "mean": "..."
    }
    """
    try:
        current_user_id = get_jwt_identity()

        req_data = request.get_json()
        phrase = req_data.get("phrase")
        mean = req_data.get("mean")

        active_learning_config = LearningConfig.query \
            .join(User) \
            .join(Language) \
            .filter(User.id == current_user_id) \
            .filter(LearningConfig.is_applying == True) \
            .first()
        
        if not active_learning_config:
            current_app.logger.error(f"学習設定が適切に設定されていません\nuser_id : {current_user_id}")
            ########## 現状500番で返しているが、本番時には学習設定を必ずしてもらう画面に遷移するために他のステータスコードを返す
            return jsonify({"msg": "学習設定が適切に設定されていません"}), 500

        language = active_learning_config.language.language
        TargetModel = get_myphrase_model(language)

        if not TargetModel:
            current_app.logger.error(f"対応する言語モデルが見つかりません: {language}")
            return jsonify({"msg": "対応していない言語です。"}), 400
        
        current_user_myphrase_num = TargetModel.query \
            .filter_by(user_id=current_user_id) \
            .count()

        if current_user_myphrase_num >= MAX_MYPHRASE_COUNT:
            current_app.logger.error(f"マイフレーズの個数が上限に達しています\nuser_id : {current_user_id}")
            return jsonify({"msg": "マイフレーズの個数が上限に達しています"}), 500

        new_phrase = TargetModel(phrase=phrase, mean=mean)

        db.session.add(new_phrase)
        db.session.commit()

        response_body={
            "msg": "マイフレーズ追加完了"
        }

        response = jsonify(response_body)

        return response, 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

## マイフレーズ削除（長谷川）
@api.route("/myphrase", methods=["DELETE"])
@jwt_required()
def myphrase_delete():
    current_app.logger.info("myphrase_delete-APIにアクセスがありました")
    """
    {
        "phrase_ids": [id, id, ...]
    }

    idはint型
    ex)"delete_ids": [1, 5, 12, 20]
    """
    try:
        current_user_id = get_jwt_identity()
        req_data = request.get_json()
        delete_ids = req_data.get("delete_ids", [])

        if not delete_ids:
            return jsonify({"msg": "削除対象が選択されていません"}), 400
        
        active_learning_config = LearningConfig.query \
            .join(User) \
            .join(Language) \
            .filter(User.id == current_user_id) \
            .filter(LearningConfig.is_applying == True) \
            .first()

        if not active_learning_config:
            current_app.logger.error(f"学習設定が適切に設定されていません\nuser_id : {current_user_id}")
            ########## 現状500番で返しているが、本番時には学習設定を必ずしてもらう画面に遷移するために他のステータスコードを返す
            return jsonify({"msg": "学習設定が適切に設定されていません"}), 500

        language = active_learning_config.language.language
        TargetModel = get_myphrase_model(language)

        if not TargetModel:
            current_app.logger.error(f"対応する言語モデルが見つかりません: {language}")
            return jsonify({"msg": "対応していない言語です。"}), 400
        
        # 削除処理
        result = TargetModel.query \
            .filter(TargetModel.id.in_(delete_ids)) \
            .filter(TargetModel.user_id == current_user_id) \
            .delete(synchronize_session=False)
        
        if result == 0:
            # 自分のデータでないマイフレーズIDが送られてきた場合などはここに来る
            return jsonify({"msg": "削除対象が見つかりませんでした"}), 404

        db.session.commit()
        
        current_app.logger.info(f"{result}件のマイフレーズを削除しました")

        res_body = {
            "msg": f"{result}件削除しました"
        }
        return jsonify(res_body), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

## マイフレーズテスト（長谷川）
@api.route("/myphrase/test", methods=["PUT"])
@jwt_required()
def test():
    current_app.logger.info("test-APIにアクセスがありました")
    """
    request.body(json)
    {
        "myphrase_question_num": "..."
    }
    """
    try:
        current_user_id = get_jwt_identity()
        req_data = request.get_json()
        raw_num = req_data.get("myphrase_question_num")
        if raw_num is None:
            return jsonify({"msg": "問題数が指定されていません"}), 400
        
        try:
            myphrase_question_num = int(raw_num)
            if myphrase_question_num <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"msg": "問題数は1以上の整数で指定してください"}), 400

        active_learning_config = LearningConfig.query \
            .join(User) \
            .join(Language) \
            .filter(User.id == current_user_id) \
            .filter(LearningConfig.is_applying == True) \
            .first()

        if not active_learning_config:
            current_app.logger.error(f"学習設定が適切に設定されていません\nuser_id : {current_user_id}")
            ########## 現状500番で返しているが、本番時には学習設定を必ずしてもらう画面に遷移するために他のステータスコードを返す
            return jsonify({"msg": "学習設定が適切に設定されていません"}), 500

        language = active_learning_config.language.language
        TargetModel = get_myphrase_model(language)

        if not TargetModel:
            current_app.logger.error(f"対応する言語モデルが見つかりません: {language}")
            return jsonify({"msg": "対応していない言語です。"}), 400
        
        questions = TargetModel.query.filter_by(user_id=current_user_id) \
            .order_by(func.random()) \
            .limit(myphrase_question_num) \
            .all()
        
        if active_learning_config.myphrase_question_num != myphrase_question_num:
            # LearningConfigのmyphrase_question_numカラム更新処理
            active_learning_config.myphrase_question_num = myphrase_question_num
            db.session.commit()

        question_list=[]
        for question in questions:
            question_list.append({
                "id": question.id,
                "phrase": question.phrase,
                "mean": question.mean
            })

        res_body = {
            "questions": question_list
        }

        return jsonify(res_body), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500

### プロフィール（秦野）
@api.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_app.logger.info("profile-APIにアクセスがありました")
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
    


""" 以下DB内容変更系APIのテンプレ """
def temp():
    current_app.logger.info("-APIにアクセスがありました")
    try:
        current_user_id = get_jwt_identity()
        req_data = request.get_json()

        db.session.commit()

        return jsonify({"msg": "成功しました"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500