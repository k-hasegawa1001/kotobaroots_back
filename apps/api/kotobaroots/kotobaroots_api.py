from flask import Blueprint, request, render_template, current_app, jsonify

from ...email import send_email

# from flask_jwt_extended import jwt_required, get_jwt_identity
### 認証
from flask_login import login_required, current_user
###

### DB
from sqlalchemy import delete, desc
from sqlalchemy.sql.expression import func

from apps.extensions import db

from apps.api.auth.models import User
from apps.api.kotobaroots.models import Contact, LearningConfig, Language, AICorrectionHistory, LearningTopic, LearningProgress, LearningHistory

### マイフレーズ（マッピング）
from apps.api.kotobaroots.utils import get_myphrase_model

### メールアドレス変更
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from apps.api.kotobaroots.utils import generate_email_change_token, verify_email_change_token

### GPT-API
import openai
import json

### 学習
import random
from .utils import load_preset_questions

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
@login_required
def contact():
    """
    お問い合わせ送信API
    
    ログイン中のユーザーからのお問い合わせを受け付け、データベースに保存します。
    ---
    tags:
      - Contact
    parameters:
      - name: body
        in: body
        required: true
        description: お問い合わせデータ
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
              example: "アプリの使い方が分かりません。教えてください。"
              description: 問い合わせ内容
    responses:
      200:
        description: 送信成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "お問い合わせが送信されました！"
      401:
        description: 認証エラー（ログインが必要）
      500:
        description: サーバー内部エラー
        schema:
          properties:
            error:
              type: string
    """
    current_app.logger.info("contact-APIにアクセスがありました")
    
    try:
        contact_data = request.get_json()
        # user_email = contact_data.get("user_email")
        current_user_id=current_user.id
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
@login_required
def myphrase():
    """
    マイフレーズ一覧取得API
    
    現在選択中の学習言語（英語など）に基づいて、ユーザーが保存したフレーズ一覧を取得します。
    あわせて、テスト実行時の「出題数設定」も返却します。
    ---
    tags:
      - MyPhrase
    responses:
      200:
        description: 取得成功
        schema:
          type: object
          properties:
            myphrases:
              type: array
              description: 保存されたフレーズのリスト
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 101
                  phrase:
                    type: string
                    example: "It's a piece of cake."
                    description: フレーズや単語
                  mean:
                    type: string
                    example: "朝飯前だ（とても簡単だ）"
                    description: 意味
            question_num:
              type: integer
              example: 10
              description: ユーザーが設定している「1回のテストでの出題数」
      400:
        description: 言語モデルエラー（対応していない言語が設定されている場合など）
        schema:
          type: object
          properties:
            msg:
              type: string
      401:
        description: 認証エラー
      500:
        description: サーバー内部エラー（または学習設定が未完了の状態）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "学習設定が適切に設定されていません"
    """
    current_app.logger.info("myphrase-APIにアクセスがありました")

    try:
        # req_data = request.get_json()
        # email = req_data.get("email")
        current_user_id=current_user.id

        # user = User.query.filter_by(email=email).first()

        # 現在適用中のlearning_configを取得
        active_learning_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
        
        if not active_learning_config:
            current_app.logger.error(f"学習設定が適切に設定されていません\nuser_id : {current_user_id}")
            ########## TODO:現状500番で返しているが、本番時には学習設定を必ずしてもらう画面に遷移するために他のステータスコードを返す
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
@login_required
def myphrase_add():
    """
    マイフレーズ追加API
    
    現在選択中の学習言語の設定に基づいて、新しいフレーズと意味をデータベースに保存します。
    ユーザーごとの保存上限数（MAX_MYPHRASE_COUNT）に達している場合はエラーを返します。
    ---
    tags:
      - MyPhrase
    parameters:
      - name: body
        in: body
        required: true
        description: 追加するフレーズ情報
        schema:
          type: object
          required:
            - phrase
            - mean
          properties:
            phrase:
              type: string
              example: "It's a piece of cake."
              description: 覚えたい単語やフレーズ
            mean:
              type: string
              example: "朝飯前だ（とても簡単だ）"
              description: その意味
    responses:
      200:
        description: 追加成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "マイフレーズ追加完了"
      400:
        description: リクエスト不正（言語モデルエラーなど）
      401:
        description: 認証エラー
      500:
        description: サーバーエラー（学習設定未完了、または登録上限数到達）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "マイフレーズの個数が上限に達しています"
    """
    current_app.logger.info("myphrase_add-APIにアクセスがありました")
    
    try:
        current_user_id = current_user.id

        req_data = request.get_json()
        phrase = req_data.get("phrase")
        mean = req_data.get("mean")

        active_learning_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
        
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

        new_phrase = TargetModel(user_id=current_user_id,phrase=phrase, mean=mean)

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
@login_required
def myphrase_delete():
    """
    マイフレーズ削除API
    
    チェックボックス等で選択された複数のマイフレーズを一括削除します。
    リクエストボディには削除したいフレーズのIDを配列（リスト）で指定します。
    他人のデータを削除できないよう、所有者チェックも内部で行われます。
    ---
    tags:
      - MyPhrase
    parameters:
      - name: body
        in: body
        required: true
        description: 削除対象のIDリスト
        schema:
          type: object
          required:
            - delete_ids
          properties:
            delete_ids:
              type: array
              description: 削除したいフレーズのIDリスト
              items:
                type: integer
              example: [1, 5, 12]
    responses:
      200:
        description: 削除成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "3件削除しました"
      400:
        description: 入力エラー（削除対象が選択されていない、対応言語エラーなど）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "削除対象が選択されていません"
      404:
        description: 対象が見つからない（指定されたIDが存在しない、または他人のデータ）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "削除対象が見つかりませんでした"
      500:
        description: サーバーエラー（学習設定未完了など）
        schema:
          type: object
          properties:
            msg:
              type: string
    """
    current_app.logger.info("myphrase_delete-APIにアクセスがありました")
    
    try:
        current_user_id = current_user.id
        req_data = request.get_json()
        delete_ids = req_data.get("delete_ids", [])

        if not delete_ids:
            return jsonify({"msg": "削除対象が選択されていません"}), 400
        
        active_learning_config = LearningConfig.query.filter_by(user_id=current_user_id).first()

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
@login_required
def test():
    """
    マイフレーズテスト作成API
    
    指定された出題数に基づいて、保存済みのマイフレーズからランダムに問題データを取得して返します。
    この時、リクエストされた出題数が現在の設定値と異なる場合は、ユーザーの学習設定（デフォルト出題数）を上書き更新します。
    ---
    tags:
      - MyPhrase
    parameters:
      - name: body
        in: body
        required: true
        description: テスト設定
        schema:
          type: object
          required:
            - myphrase_question_num
          properties:
            myphrase_question_num:
              type: integer
              example: 10
              description: 今回の出題数（UI上の選択肢は 10, 30, 50, 100 など）
    responses:
      200:
        description: テストデータ生成成功
        schema:
          type: object
          properties:
            questions:
              type: array
              description: ランダムに選出された問題データのリスト
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 101
                  phrase:
                    type: string
                    example: "It's a piece of cake."
                    description: 問題文（または解答）となるフレーズ
                  mean:
                    type: string
                    example: "朝飯前だ（とても簡単だ）"
                    description: 解答（または問題文）となる意味
      400:
        description: 入力エラー（数値でない、0以下など）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "問題数は1以上の整数で指定してください"
      500:
        description: サーバーエラー（学習設定未完了など）
        schema:
          type: object
          properties:
            msg:
              type: string
    """
    current_app.logger.info("test-APIにアクセスがありました")
    
    try:
        current_user_id = current_user.id
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

        active_learning_config = LearningConfig.query.filter_by(user_id=current_user_id).first()

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

### プロフィール
## トップ（秦野）
@api.route("/profile", methods=["GET"])
@login_required
def profile():
    """
    プロフィール情報取得API
    
    現在ログインしているユーザーの基本情報（ユーザー名、メールアドレス、登録日時）を取得します。
    ---
    tags:
      - Profile
    responses:
      200:
        description: 取得成功
        schema:
          type: object
          properties:
            username:
              type: string
              example: "テストユーザー"
              description: ユーザー名
            email:
              type: string
              example: "test@example.com"
              description: メールアドレス
            created_at:
              type: string
              example: "2023-10-01 12:00:00"
              description: アカウント作成日時 (YYYY-MM-DD HH:MM:SS)
      401:
        description: 認証エラー（ログインが必要）
      404:
        description: ユーザーが見つからない（削除済みなど）
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: サーバー内部エラー
        schema:
          type: object
          properties:
            error:
              type: string
    """
    current_app.logger.info("profile-APIにアクセスがありました")
    """
    request.body(json)
    {
    
    }
    """
    try:
        user_id = current_user.id
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

## ユーザー名変更（秦野）
@api.route("/profile/username", methods=["PATCH"])
@login_required
def update_username():
    """
    ユーザー名変更API
    
    ログイン中のユーザーの表示名（username）を変更します。
    変更前と同じ名前が送信された場合は、DB更新を行わずに成功レスポンスを返します。
    ---
    tags:
      - Profile
    parameters:
      - name: body
        in: body
        required: true
        description: 新しいユーザー名
        schema:
          type: object
          required:
            - username
          properties:
            username:
              type: string
              example: "NewUserName123"
              description: 変更後のユーザー名
    responses:
      200:
        description: 更新成功（または変更なし）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "ユーザー名を更新しました"
      400:
        description: 入力エラー（usernameが空など）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "username が必要です"
      401:
        description: 認証エラー
      404:
        description: ユーザーが見つからない
      500:
        description: サーバー内部エラー
    """
    current_app.logger.info("update_username-APIにアクセスがありました")
    try:
        current_user_id = current_user.id
        data = request.get_json()
        new_username = data.get("username")

        if not new_username:
            return jsonify({"msg": "username が必要です"}), 400

        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"msg": "ユーザーが見つかりません"}), 404

        if user.username == new_username:
            # いちいち更新しなくて良い場合
            return jsonify({"msg": "ユーザー名を更新しました"}), 200

        user.username = new_username
        db.session.commit()

        return jsonify({"msg": "ユーザー名を更新しました"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": str(e)}), 500

## メールアドレス変更（メール送信）（秦野）
@api.route("/profile/email/request", methods=["POST"])
@login_required
def request_change_email():
    """
    メールアドレス変更申請API
    
    新しいメールアドレス宛に、有効性確認のためのトークン付きURLを記載したメールを送信します。
    このAPIを叩いただけでは、ユーザー情報はまだ更新されません（メール内のリンクを踏んだ時点で完了となります）。
    ---
    tags:
      - Profile
    parameters:
      - name: body
        in: body
        required: true
        description: 変更したい新しいメールアドレス
        schema:
          type: object
          required:
            - new_email
          properties:
            new_email:
              type: string
              example: "new_address@example.com"
              description: 新しいメールアドレス
    responses:
      200:
        description: メール送信成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "確認メールを送信しました"
      400:
        description: 入力エラー（メールアドレス未入力、または既に使用されている）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "このメールアドレスは既に使用されています"
      401:
        description: 認証エラー
      500:
        description: サーバー内部エラー（メール送信失敗など）
    """
    current_app.logger.info("request_change_email-APIにアクセスがありました")
    current_user_id = current_user.id
    data = request.get_json()
    new_email = data.get("new_email")

    if not new_email:
        return jsonify({"msg": "新しいメールアドレスが必要です"}), 400

    # すでに存在していないかチェック
    exists = User.query.filter_by(email=new_email).first()
    current_app.logger.info(f"メールアドレス変更申請: user_id={current_user_id}, new_email={new_email}, exists={exists is not None}")
    if exists:
        return jsonify({"msg": "このメールアドレスは既に使用されています"}), 400

    # トークン生成
    # s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    # token = s.dumps({"user_id": current_user_id, "new_email": new_email})
    token = generate_email_change_token(current_user_id, new_email)

    frontend_url = current_app.config.get("FRONTEND_URL", "http://127.0.0.1:5500")
    confirm_url = f"{frontend_url}/profile/edit-email-confirmation.html?token={token}"

    # メール送信
    send_email(
        to=new_email,
        subject="メールアドレス変更の確認",
        template="change_email/change_email",
        confirm_url=confirm_url
    )

    return jsonify({"msg": "確認メールを送信しました"}), 200

# ## トークン検証（秦野）
# @api.route("/profile/email/confirm/<token>", methods=["GET"])
# def confirm_change_email_token(token):
#     """
#     フロントエンドが画面を表示する前に、「このトークン生きてる？」を確認するためのAPI
#     """
#     payload = verify_email_change_token(token)
    
#     if not payload:
#         return jsonify({"msg": "無効、または期限切れのリンクです"}), 400

#     # 問題なければ、変更しようとしているメアドなどを返す（画面表示用）
#     return jsonify({
#         "msg": "トークンは有効です",
#         "new_email": payload["new_email"]
#     }), 200

## メールアドレス変更処理（秦野）
"""
【注意点】
もしユーザーがスマホで申請し、PCでメールを開いた場合（PCで未ログインの場合）、
フローの最後で 401 Unauthorized エラーになる

その場合、フロントエンドは「ログインしてください」と
ログイン画面へ誘導する処理が必要になる
"""
@api.route("/profile/email/update", methods=["POST"])
@login_required
def update_email():
    """
    メールアドレス変更実行API
    
    メール内のリンクから取得したトークンと、本人確認用のパスワードを検証し、
    問題がなければメールアドレスを正式に更新します。
    
    【重要：フロントエンド実装時の注意】
    このAPIは `@login_required` により保護されています。
    もしユーザーが「スマホで申請」し、「PC（未ログイン状態）でメールリンクを開いた」場合、
    このAPIは `401 Unauthorized` を返します。
    その場合、フロントエンドはユーザーをログイン画面へ誘導する必要があります。
    ---
    tags:
      - Profile
    parameters:
      - name: body
        in: body
        required: true
        description: トークンとパスワード
        schema:
          type: object
          required:
            - token
            - password
          properties:
            token:
              type: string
              example: "Im5ld19..."
              description: メールリンクのクエリパラメータ(?token=...)から取得した文字列
            password:
              type: string
              example: "password123"
              description: 本人確認用のログインパスワード
    responses:
      200:
        description: 更新成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "メールアドレスを更新しました"
      400:
        description: 検証エラー（トークン無効・期限切れ、またはパスワード間違い）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "無効、または期限切れのトークンです"
      401:
        description: 認証エラー（未ログイン状態でアクセスした）
      403:
        description: 権限エラー（トークンの申請者と現在ログインしているユーザーが異なる）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "不正なリクエストです"
      500:
        description: サーバー内部エラー
    """
    try:
        current_user_id = current_user.id
        data = request.get_json()

        token = data.get("token")
        password = data.get("password")

        if not token or not password:
            return jsonify({"msg": "トークンとパスワードが必要です"}), 400

        # トークンの検証
        payload = verify_email_change_token(token)
        if not payload:
            return jsonify({"msg": "無効、または期限切れのトークンです"}), 400

        # トークン内のユーザーIDと、現在ログイン中のユーザーIDが一致するか確認
        if payload["user_id"] != current_user_id:
            return jsonify({"msg": "不正なリクエストです"}), 403

        # パスワード確認
        user = User.query.get(current_user_id)
        if not user.check_password(password):
            return jsonify({"msg": "パスワードが違います"}), 400

        # メールアドレス更新処理
        user.email = payload["new_email"]
        db.session.commit()

        return jsonify({"msg": "メールアドレスを更新しました"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500

### AI解説
## トップ（長谷川）
@api.route("/ai-explanation", methods=["GET", "POST"])
@login_required
def ai_explanation():
    """
    AI英文解説・添削API
    
    ユーザーが入力した任意の外国語文（学習中の言語：学習設定に紐づいている言語）を受け取り、AI（GPT-4o-mini）がその意味（翻訳）と、
    文化的・歴史的背景を含めた詳しい解説を生成して返します。
    同時に、生成結果を履歴（AICorrectionHistory）として保存します。
    ---
    tags:
      - AI-Explanation
    parameters:
      - name: body
        in: body
        required: true
        description: 解説してほしい外国語文
        schema:
          type: object
          required:
            - input_string
          properties:
            input_string:
              type: string
              example: ":)"
              description: 解析対象のテキスト（英文、スラング、顔文字など）
    responses:
      200:
        description: 生成成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "解説生成成功"
            translation:
              type: string
              description: AIによる翻訳
              example: "笑顔（スマイリーフェイス）"
            explanation:
              type: string
              description: AIによる文化的・歴史的背景の解説
              example: "欧米圏で広く使われる顔文字です。首を左に90度傾けて見ると笑顔に見えることから来ています。"
      400:
        description: リクエスト不正（テキスト未入力、または学習設定未完了）
        schema:
          type: object
          properties:
            msg:
              type: string
      500:
        description: サーバー内部エラー（OpenAI APIエラーなど）
    """
    if request.method == "GET":
        # おそらく使われることはない
        current_app.logger.info("ai_explanation-API（GET）にアクセスがありました")
        return jsonify({"msg": "AI解説トップページ"}), 200

    # POSTリクエスト: ChatGPT解説生成
    if request.method == "POST":
        current_app.logger.info("ai_explanation-API（POST）にアクセスがありました")
        
        """
        {
            "input_string": "..."
        }
        """
        current_user_id = current_user.id
        req_data = request.get_json()
        input_string = req_data.get("input_string")

        try:
            if not input_string:
                    return jsonify({"msg": "テキストが入力されていません"}), 400
            
            active_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
            
            if not active_config:
                    return jsonify({"msg": "学習設定が見つかりません"}), 400
                
            language_id = active_config.language.id
            # 綴りが同じだが、言語によって意味が異なる場合もあるため、現在学習中の言語もプロンプトに含める必要がある
            language_name = active_config.language.language # 学習中の言語

            # OpenAI APIの準備
            client = openai.OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

            prompt = f"" # TODO: プロンプトが作成完了次第埋め込み

            # APIリクエスト (gpt-4o-mini)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": input_string}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )

            ai_content = response.choices[0].message.content
            result_json = json.loads(ai_content) # 文字列を辞書型に変換

            translation = result_json.get("translation", "")
            explanation = result_json.get("explanation", "")

            new_history = AICorrectionHistory(
                user_id=current_user_id,
                language_id=language_id,
                input_string=input_string,
                japanese_translation=translation,
                explanation=explanation
                # created_atはデフォルトで入るので指定不要
            )

            db.session.add(new_history)
            db.session.commit()

            # 7. フロントへ返却
            return jsonify({
                "msg": "解説生成成功",
                "translation": translation,
                "explanation": explanation
            }), 200

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"AI生成エラー: {e}")
            return jsonify({"msg": "AI生成中にエラーが発生しました", "error": str(e)}), 500

## 履歴（長谷川）
@api.route("/ai-explanation/history", methods=["GET"])
@login_required
def ai_explanation_history():
    """
    AI解説履歴取得API
    
    ログインユーザーの過去のAI解説履歴を日時降順（新しい順）で全件取得します。
    
    【仕様上の注意】
    データの保持期間は作成から3ヶ月間です。それ以上経過したデータは自動的に削除されるため、
    履歴一覧には含まれません。
    ---
    tags:
      - AI-Explanation
    responses:
      200:
        description: 取得成功（履歴のリスト）
        schema:
          type: array
          description: 履歴オブジェクトの配列
          items:
            type: object
            properties:
              id:
                type: integer
                example: 10
              input_english:
                type: string
                example: "brb"
                description: ユーザーが入力した英文
              japanese_translation:
                type: string
                example: "すぐ戻ります (Be right back)"
                description: AIによる翻訳結果
              explanation:
                type: string
                example: "オンラインチャットで離席する際によく使われる略語です。"
                description: AIによる解説
              created_at:
                type: string
                example: "2023-10-25 14:30:00"
                description: 作成日時 (YYYY-MM-DD HH:MM:SS形式)
      401:
        description: 認証エラー（ログインが必要）
      500:
        description: サーバー内部エラー
    """
    current_app.logger.info("ai_explanation_history-APIにアクセスがありました")
    current_user_id = current_user.id

    # 履歴の一覧を取得
    ai_explanation_histories = AICorrectionHistory.query \
        .filter_by(user_id=current_user_id) \
        .order_by(desc(AICorrectionHistory.created_at)) \
        .all()
    
    response_histories = []
    for ai_explanation_history in ai_explanation_histories:
        response_histories.append({
            "id": ai_explanation_history.id,
            "input_english": ai_explanation_history.input_english,
            "japanese_translation": ai_explanation_history.japanese_translation,
            "explanation": ai_explanation_history.explanation,
            # フロントで扱いやすいように日付は文字列に変換しておく
            "created_at": ai_explanation_history.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(response_histories), 200

### 学習
## トップ（長谷川）
# http://127.0.0.1:5000/api/kotobaroots/learning
@api.route("/learning", methods=["GET"])
@login_required
def learning_index():
    """
    学習単元一覧取得API
    
    現在の学習設定（言語・レベル）に基づいて、学習可能な単元の一覧と、
    ユーザーの現在の進捗（どこまで解放されているか）を返します。
    ---
    tags:
      - Learning
    responses:
      200:
        description: 取得成功
        schema:
          type: object
          properties:
            learning_topics:
              type: array
              description: 単元のリスト（難易度順）
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  topic:
                    type: string
                    example: "基本文法 - 現在形"
                  difficulty:
                    type: integer
                    example: 1
            current_max_difficulty:
              type: integer
              description: 現在解放されている難易度の上限（これ以下のdifficultyを持つ単元が選択可能）
              example: 5
      400:
        description: 学習設定が見つからない（初期設定が完了していない）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "学習設定が見つかりません"
      401:
        description: 認証エラー
      500:
        description: サーバー内部エラー
        schema:
          properties:
            msg:
              type: string
    """
    current_app.logger.info("learning_index-APIにアクセスがありました")
    current_user_id = current_user.id

    try:
        active_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
            
        if not active_config:
            return jsonify({"msg": "学習設定が見つかりません"}), 400
        
        language_id = active_config.language.id
        level_id = active_config.level.id

        learning_topic_list = LearningTopic.query \
            .filter_by(level_id=level_id, language_id=language_id) \
            .order_by(LearningTopic.difficulty) \
            .all()

        # unlocked_topic = UnlockedTopic.query \
        #     .join(LearningTopic) \
        #     .filter(UnlockedTopic.user_id==current_user_id) \
        #     .filter(LearningTopic.language_id==language_id) \
        #     .filter(LearningTopic.level_id==level_id) \
        #     .first()

        progress = LearningProgress.query.filter_by(
            user_id=current_user_id,
            language_id=language_id,
            level_id=level_id
        ).first()

        # レコードがなければ初期状態（難易度1）
        current_max_difficulty = progress.current_difficulty if progress else 1
        
        response_learning_topics = []
        for learning_topic in learning_topic_list:
            response_learning_topics.append({
                "id": learning_topic.id,
                "topic": learning_topic.topic,
                "difficulty": learning_topic.difficulty
            })
        
        response = jsonify({"learning_topics": response_learning_topics, "current_max_difficulty": current_max_difficulty})

        return response, 200
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500

## 問題生成（長谷川）
@api.route("/learning/generate-questions", methods=["POST"])
@login_required
def generate_questions():
    """
    問題自動生成API (OpenAI連携)
    
    指定された学習単元（Topic）に基づいて、OpenAI API (GPT-4o-mini) を使用して
    文法問題（4択、穴埋め、並び替え）をランダムに9問生成して返します。
    ---
    tags:
      - Learning
    parameters:
      - name: body
        in: body
        required: true
        description: 問題作成の条件
        schema:
          type: object
          required:
            - learning_topic_id
          properties:
            learning_topic_id:
              type: integer
              example: 1
              description: 対象の単元ID
    responses:
      200:
        description: 生成成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "問題生成成功"
            topic_id:
              type: integer
              example: 1
            country:
              type: string
              example: "USA"
              description: 言語に関連する国（解説の文化的背景などに使用）
            questions:
              type: array
              description: 生成された問題リスト（全9問）
              items:
                type: object
                properties:
                  question_format:
                    type: string
                    example: "Multiple Choice"
                    description: 問題形式（Multiple Choice / Fill-in-the-blank / Sentence Rearrangement）
                  question:
                    type: string
                    example: "「私は猫が好きです」を英語にしなさい。"
                  options:
                    type: array
                    description: 選択肢のリスト（並び替え問題の場合はシャッフルされた単語リスト）
                    items:
                      type: string
                    example: ["I like cats.", "I like dogs.", "I hate cats.", "Cats like me."]
                  answer:
                    type: string
                    description: 正解の文字列
                    example: "I like cats."
                  explanation:
                    type: string
                    description: 日本語による解説（文化的背景含む）
      400:
        description: リクエスト不正（単元ID未指定など）
        schema:
          type: object
          properties:
            msg:
              type: string
      404:
        description: 対象の単元が見つからない
      500:
        description: サーバー内部エラー（OpenAI APIエラーなど）
    """
    current_app.logger.info("generate_questions-APIにアクセスがありました")
    
    current_user_id = current_user.id
    req_data = request.get_json()
    target_topic_id = req_data.get("learning_topic_id")

    try:
        # active_config = LearningConfig.query \
        #     .join(User).join(Language) \
        #     .filter(User.id == current_user_id) \
        #     .filter(LearningConfig.is_applying == True) \
        #     .first()
            
        # if not active_config:
        #     return jsonify({"msg": "学習設定が見つかりません"}), 400
        
        if not target_topic_id:
            return jsonify({"msg": "学習単元IDが指定されていません"}), 400
        
        target_topic = LearningTopic.query.get(target_topic_id)
        if not target_topic:
            return jsonify({"msg": "指定された学習単元が見つかりません"}), 404

        ## プロンプト変数
        country = target_topic.language.country
        language_name = target_topic.language.language
        level = target_topic.level.level_tag

        ## OpenAI APIの準備
        client = openai.OpenAI(api_key=current_app.config["OPENAI_API_KEY"])

        ## 問題形式のランダム選択と詳細指示の定義
        # (日本語訳選択 / 穴埋め / 並び替え)
        all_formats_rules = """
        1. "Multiple Choice":
           - Question: Provide a natural Japanese sentence.
           - Options: 4 English sentences. 1 correct translation, 3 incorrect.
           - Answer: The correct English sentence string.

        2. "Fill-in-the-blank":
           - Question: Provide an English sentence with a single blank (represented by '___').
           - Options: 4 choices (words or phrases).
           - Answer: The correct word/phrase string.

        3. "Sentence Rearrangement":
           - Question: Provide a natural Japanese sentence.
           - Options: A list of shuffled English words/phrases that form the correct translation.
           - Answer: The correct full English sentence string.
        """

        system_prompt = f"""
        You are a native {language_name} speaker living in {country}.
        Create {language_name} grammar questions in JSON format.
        
        Output Structure (JSON):
        {{
            "learning_topic": "...",
            "questions": [
                {{
                    "question_format": "Multiple Choice" or "Fill-in-the-blank" or "Sentence Rearrangement",
                    "question": "Question text...",
                    "options": ["opt1", "opt2", ...],
                    "answer": "Correct answer string",
                    "explanation": "Explanation in Japanese (200-500 chars). Include cultural nuances of {country}."
                }},
                ...
            ]
        }}
        """

        user_prompt = f"""
        Create a total of 9 questions based on the topic "{target_topic.topic}" (Difficulty: {target_topic.difficulty}).
        
        Important Instructions:
        - Randomly mix the 3 question formats ("Multiple Choice", "Fill-in-the-blank", "Sentence Rearrangement") within the 9 questions.
        - Do NOT simply create 3 of each. The distribution should be random.
        - Shuffle the order of the questions.
        
        Format Rules:
        {all_formats_rules}
        
        Explanation:
        - Must be in Japanese.
        - Include cultural background or usage nuances specific to {country}.
        """

        # APIリクエスト (gpt-4o-mini)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        ai_content = response.choices[0].message.content
        result_json = json.loads(ai_content)
        
        questions = result_json.get("questions", [])
        return jsonify({
            "msg": "問題生成成功",
            "topic_id": target_topic_id,
            "country": country,
            "questions": questions
        }), 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500

## 学習開始（問題プリセット取得）（長谷川）
@api.route("/learning/start", methods=["POST"])
@login_required
def learning_start():
    """
    学習開始API（プリセット問題取得）
    
    指定された単元IDに対応する、サーバー内に保存された教材データ（JSONファイル）を読み込んで返します。
    DBの学習単元情報（言語、国、レベル、トピックキー）に基づいて、適切なファイルのパスを自動的に解決します。
    ---
    tags:
      - Learning
    parameters:
      - name: body
        in: body
        required: true
        description: 学習開始リクエスト
        schema:
          type: object
          required:
            - learning_topic_id
          properties:
            learning_topic_id:
              type: integer
              example: 1
              description: 開始する単元のID
    responses:
      200:
        description: 取得成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "プリセット問題取得成功"
            topic_id:
              type: integer
              example: 1
            topic_title:
              type: string
              example: "基本の挨拶"
              description: フロントエンド表示用の単元タイトル
            questions:
              type: array
              description: 問題リスト
              items:
                type: object
                properties:
                  question_format:
                    type: string
                    example: "Multiple Choice"
                  question:
                    type: string
                    example: "「ありがとう」を英語にしなさい。"
                  options:
                    type: array
                    items:
                      type: string
                    example: ["Thank you.", "Hello.", "Goodbye.", "Sorry."]
                  answer:
                    type: string
                    example: "Thank you."
                  explanation:
                    type: string
                    example: "感謝を伝える基本的な表現です。"
      400:
        description: リクエスト不正（ID未指定など）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "学習単元IDが指定されていません"
      401:
        description: 認証エラー
      404:
        description: 指定された単元がDBに存在しない
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "指定された学習単元が見つかりません"
      500:
        description: サーバー内部エラー（教材ファイルが見つからない、または空の場合など）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "教材データの取得に失敗しました（ファイルが見つかりません）"
    """
    current_app.logger.info("learning_start-APIにアクセスがありました")
    
    # リクエストからデータを取得
    req_data = request.get_json()
    target_topic_id = req_data.get("learning_topic_id")

    if not target_topic_id:
        return jsonify({"msg": "学習単元IDが指定されていません"}), 400

    try:
        # DBから学習単元情報を取得（リレーション先の Language, Level も必要）
        target_topic = LearningTopic.query.get(target_topic_id)
        
        if not target_topic:
            return jsonify({"msg": "指定された学習単元が見つかりません"}), 404

        # ---------------------------------------------------------
        # パス情報の構築 (DBの値 → フォルダ名への変換)
        # ---------------------------------------------------------
        
        # 1. Language: "English" -> "english"
        if not target_topic.language:
             return jsonify({"msg": "言語設定エラー: この単元には言語が紐付いていません"}), 500
        lang_folder = target_topic.language.language.lower()

        # 2. Country: "America" -> "america"
        # countryがNULLの場合は適宜ハンドリングが必要ですが、
        # ディレクトリ構造上必須であれば以下のように取得
        country_folder = target_topic.language.country.lower() if target_topic.language.country else "default"

        # 3. Level: "Beginner" -> "beginner"
        # Levelモデルの level_tag カラムを使用
        level_folder = target_topic.level.level_tag.lower()

        # 4. Filename: "subjunctive_mood"
        # ここでは topic カラムの値をそのままファイル名として使用します
        # ※ もしDBの topic が日本語（例："仮定法"）の場合は、
        #    LearningTopicモデルに `file_key` カラムを追加することを推奨します。
        topic_filename = target_topic.topic_key

        # ---------------------------------------------------------
        # 問題データの取得
        # ---------------------------------------------------------
        questions_data = load_preset_questions(
            language=lang_folder,
            country=country_folder,
            level=level_folder,
            topic_filename=topic_filename,
            limit=10  # 1回あたりの出題数
        )

        if questions_data is None:
            return jsonify({"msg": "教材データの取得に失敗しました（ファイルが見つかりません）"}), 500

        if len(questions_data) == 0:
            return jsonify({"msg": "問題データが空です"}), 500

        # ---------------------------------------------------------
        # レスポンス返却
        # ---------------------------------------------------------
        return jsonify({
            "msg": "プリセット問題取得成功",
            "topic_id": target_topic.id,
            "topic_title": target_topic.topic, # フロント表示用のタイトル
            "questions": questions_data
        }), 200

    except Exception as e:
        current_app.logger.error(f"learning_start API Error: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"msg": "サーバー内部エラーが発生しました"}), 500
    
## 学習完了（長谷川）
@api.route("/learning/complete", methods=["POST"])
@login_required
def learning_complete():
    """
    学習完了・履歴保存API
    
    学習終了時に呼び出し、回答結果の履歴保存と学習進捗（難易度解放）の更新を行います。
    リクエストには、実施した単元IDと、各問題の回答結果リスト（履歴データ）を含めます。
    ---
    tags:
      - Learning
    parameters:
      - name: body
        in: body
        required: true
        description: 学習結果データ
        schema:
          type: object
          required:
            - learning_topic_id
            - results
          properties:
            learning_topic_id:
              type: integer
              example: 1
              description: 実施した単元のID
            results:
              type: array
              description: 各問題の回答結果リスト
              items:
                type: object
                properties:
                  is_passed:
                    type: boolean
                    example: true
                    description: 正解したかどうか
                  question_statement:
                    type: string
                    example: "「ありがとう」を英語にしなさい。"
                  choices:
                    type: array
                    items: 
                      type: string
                    example: ["Thank you", "Hello"]
                    description: 提示された選択肢のリスト
                  correct_answer:
                    type: string
                    example: "Thank you"
                    description: 正解の文字列
                  explanation:
                    type: string
                    example: "感謝を伝える表現です。"
                  user_answer:
                    type: string
                    example: "Thank you"
                    description: ユーザーが選んだ回答
    responses:
      200:
        description: 保存成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "学習履歴を保存しました"
            progress_updated:
              type: boolean
              example: true
              description: 難易度レベルが上がったかどうか
            new_difficulty:
              type: integer
              example: 2
              description: 現在の到達難易度
      400:
        description: 入力エラー
      500:
        description: サーバー内部エラー
    """
    current_app.logger.info("learning_complete-APIにアクセスがありました")
    
    current_user_id = current_user.id
    req_data = request.get_json()
    
    topic_id = req_data.get("learning_topic_id")
    results = req_data.get("results", [])

    if not topic_id or not results:
        return jsonify({"msg": "必要なデータが不足しています"}), 400

    try:
        # 1. 履歴の保存 (一括処理)
        passed_count = 0 # 正解数カウント
        
        for res in results:
            is_passed = res.get("is_passed", False)
            if is_passed:
                passed_count += 1
            
            # 選択肢配列を文字列(JSON)に変換
            choices_list = res.get("choices", [])
            choices_str = json.dumps(choices_list, ensure_ascii=False)

            # 正解している場合は correct_answer を NULL (None) にする仕様
            correct_answer_val = None if is_passed else res.get("correct_answer")

            history = LearningHistory(
                user_id=current_user_id,
                learning_topic_id=topic_id,
                is_passed=is_passed,
                question_statement=res.get("question_statement", ""),
                choices=choices_str,
                correct_answer=correct_answer_val,
                explanation=res.get("explanation", ""),
                user_answer=res.get("user_answer", "")
            )
            db.session.add(history)
        
        # 2. 進捗 (LearningProgress) の更新判定
        # ここでは「正答率80%以上」で次の難易度を解放するロジックとします
        # 必要に応じて閾値（0.8）は調整してください
        total_questions = len(results)
        progress_updated = False
        
        # 現在の設定を取得して、対象のProgressを特定
        active_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
        
        if active_config and total_questions > 0:
            target_lang_id = active_config.language_id
            target_level_id = active_config.level_id
            
            # 現在の進捗レコードを取得
            progress = LearningProgress.query.filter_by(
                user_id=current_user_id,
                language_id=target_lang_id,
                level_id=target_level_id
            ).first()

            current_difficulty = progress.current_difficulty if progress else 1
            
            # 実施した単元の情報を取得（難易度チェック用）
            target_topic = LearningTopic.query.get(topic_id)
            
            # 「今挑戦した単元の難易度」が「現在の到達難易度」と同じで、かつ合格点ならレベルアップ
            if target_topic and target_topic.difficulty == current_difficulty:
                accuracy = passed_count / total_questions
                if accuracy >= 0.8: # 80%以上で合格
                    if progress:
                        progress.current_difficulty += 1
                    else:
                        # 万が一progressがない場合は作成(基本ありえないが念のため)
                        new_progress = LearningProgress(
                            user_id=current_user_id, 
                            language_id=target_lang_id, 
                            level_id=target_level_id, 
                            current_difficulty=2
                        )
                        db.session.add(new_progress)
                    
                    progress_updated = True
                    current_difficulty += 1 # レスポンス用にインクリメント

        db.session.commit()

        return jsonify({
            "msg": "学習履歴を保存しました",
            "progress_updated": progress_updated,
            "new_difficulty": current_difficulty if 'current_difficulty' in locals() else 1
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました", "error": str(e)}), 500


## 履歴（長谷川）
@api.route("/learning/history", methods=["GET"])
@login_required
def learning_history():
    """
    学習履歴一覧取得API
    
    現在の学習設定（言語・レベル）に基づいて、ユーザーの過去の学習履歴を取得します。
    新しい順（作成日の降順）で返却されます。
    ---
    tags:
      - Learning
    responses:
      200:
        description: 取得成功
        schema:
          type: object
          properties:
            histories:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 101
                  topic:
                    type: string
                    example: "基本の挨拶"
                  question:
                    type: string
                    example: "「ありがとう」を英語にしなさい。"
                  user_answer:
                    type: string
                    example: "Thank you."
                  correct_answer:
                    type: string
                    description: ユーザーが正解していた場合はnull
                    example: null
                  is_passed:
                    type: boolean
                    example: true
                  created_at:
                    type: string
                    example: "2023-10-25 14:30:00"
      400:
        description: 学習設定未完了
      500:
        description: サーバー内部エラー
    """
    current_app.logger.info("learning_history-APIにアクセスがありました")
    current_user_id = current_user.id

    try:
        # 1. 現在の学習設定を取得
        active_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
        
        if not active_config:
            return jsonify({"msg": "学習設定が見つかりません"}), 400

        target_lang_id = active_config.language_id
        target_level_id = active_config.level_id

        # 2. 履歴の取得
        # LearningHistory と LearningTopic を結合し、
        # 「現在の設定と同じ言語・レベル」かつ「自分のデータ」を検索
        histories = LearningHistory.query \
            .join(LearningTopic, LearningHistory.learning_topic_id == LearningTopic.id) \
            .filter(LearningHistory.user_id == current_user_id) \
            .filter(LearningTopic.language_id == target_lang_id) \
            .filter(LearningTopic.level_id == target_level_id) \
            .order_by(desc(LearningHistory.created_at)) \
            .all()

        # 3. レスポンスデータの整形
        response_list = []
        for h in histories:
            # 選択肢はJSON文字列なのでリストに戻す（表示に必要であれば）
            # choices_list = json.loads(h.choices) if h.choices else []

            response_list.append({
                "id": h.id,
                "topic": h.learning_topic.topic, # 単元名
                "question": h.question_statement,
                "user_answer": h.user_answer,
                "correct_answer": h.correct_answer, # 正解時はNone(null)が入っている
                "explanation": h.explanation,
                "is_passed": h.is_passed,
                "created_at": h.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify({"histories": response_list}), 200

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました", "error": str(e)}), 500


## 学習設定変更（長谷川）
@api.route("/learning/config", methods=["PUT"])
@login_required
def update_learning_config():
    """
    学習設定変更API
    
    ユーザーの学習設定（レベルや学習言語）を変更します。
    変更後の設定に対応する進捗データ（セーブデータ）が存在しない場合は、自動的に新規作成（初期化）します。
    ---
    tags:
      - Learning
    parameters:
      - name: body
        in: body
        required: true
        description: 変更後の設定ID
        schema:
          type: object
          properties:
            level_id:
              type: integer
              example: 2
              description: 変更したいレベルID (必須)
            language_id:
              type: integer
              example: 1
              description: 変更したい言語ID (任意。送信されない場合は現在の言語を維持)
    responses:
      200:
        description: 設定変更成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "学習設定を変更しました"
      400:
        description: 入力エラー（無効なIDなど）
      404:
        description: 指定されたレベルや言語の教材が存在しない
      500:
        description: サーバー内部エラー
    """
    current_app.logger.info("update_learning_config-APIにアクセスがありました")
    
    current_user_id = current_user.id
    req_data = request.get_json()
    
    # 変更したいIDを取得
    new_level_id = req_data.get("level_id")
    new_language_id = req_data.get("language_id")

    if new_level_id is None:
        return jsonify({"msg": "レベルIDが指定されていません"}), 400

    try:
        # 1. 現在適用中の設定を取得
        active_learning_config = LearningConfig.query.filter_by(user_id=current_user_id).first()
        
        if not active_learning_config:
            # 万が一設定がない場合は作成するロジックを入れても良いが、基本はエラー
            return jsonify({"msg": "現在の学習設定が見つかりません"}), 500

        # 2. 更新後のIDを確定させる
        # language_idが送られてこなかった場合は、元のまま維持する
        target_language_id = new_language_id if new_language_id is not None else active_learning_config.language_id
        target_level_id = new_level_id

        # 3. 【安全性チェック】その言語・レベルの教材(Topic)がそもそも存在するか確認
        # 例えば「フランス語・レベル5」を選んだけど、教材がまだ登録されていない場合などを防ぐ
        topic_exists = LearningTopic.query.filter_by(
            language_id=target_language_id,
            level_id=target_level_id
        ).first()

        if not topic_exists:
            return jsonify({"msg": "選択された設定に対応する学習教材がまだありません"}), 404

        # 4. 設定の更新
        active_learning_config.level_id = target_level_id
        active_learning_config.language_id = target_language_id

        # 5. 進捗データ(LearningProgress)の確認と作成
        # 「その設定で遊んだことがあるか？」を確認
        progress = LearningProgress.query.filter_by(
            user_id=current_user_id,
            language_id=target_language_id,
            level_id=target_level_id
        ).first()

        if not progress:
            # 遊んだことがなければ、セーブデータを新規作成（難易度1から）
            new_progress = LearningProgress(
                user_id=current_user_id,
                language_id=target_language_id,
                level_id=target_level_id,
                current_difficulty=1
            )
            db.session.add(new_progress)
            current_app.logger.info(f"新しい進捗データを作成しました: user={current_user_id}, lang={target_language_id}, level={target_level_id}")
        else:
            current_app.logger.info(f"既存の進捗データを使用します: difficulty={progress.current_difficulty}")

        db.session.commit()

        return jsonify({"msg": "学習設定を変更しました"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "設定変更中にエラーが発生しました", "error": str(e)}), 500


""" 以下DB内容変更系APIのテンプレ """
def temp():
    current_app.logger.info("-APIにアクセスがありました")
    try:
        current_user_id = current_user.id
        req_data = request.get_json()

        db.session.commit()

        return jsonify({"msg": "成功しました"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"msg": "エラーが発生しました"}), 500


## 蟄ｦ鄙貞腰蜈・ｸ隕ｧ蜿門ｾ輸PI(繧ｲ繧ｹ繝医・繝ｭ繧ｰ繧､繝ｳ荳ｭ)
@api.route("/learning/guest", methods=["GET"])
def learning_guest():
    """
    繧ｲ繧ｹ繝医・縺ｮ蟄ｦ鄙貞腰蜈・ｸ隕ｧ蜿門ｾ輸PI

    繝ｭ繧ｰ繧､繝ｳ荳ｭ縺ｫ繧医ｊ隱崎ｨｼ縺ｪ縺励・縲√後ユ繧ｹ繝医・繝ｭ繧ｰ繧､繝ｳ鐃・繧悟・繧後※繧医≧縺ｫ縺呻ｼ・
    迴ｾ蝨ｨ縺ｮ險ｭ螳壹→縺ｯ繝ｪ繝ｳ繧ｯ縺励↑縺・縺ｮ縺ｧ縲∫現在縺ｯ螳滓命縺励◆險ｭ螳壹↓蟇ｾ蠢懊☆繧九蜊伜・縺ｮ繝ｪ繧ｹ繝医・繧ｿ縺ｮ縺ｿ繧返却。
    ---
    tags:
      - Learning
    parameters:
      - name: level_id
        in: query
        required: false
        description: 難易度ID
        type: integer
      - name: language_id
        in: query
        required: false
        description: 言語ID
        type: integer
    responses:
      200:
        description: 蜿門ｾ玲・蜉・
        schema:
          type: object
          properties:
            learning_topics:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  topic:
                    type: string
                  difficulty:
                    type: integer
            current_max_difficulty:
              type: integer
      404:
        description: 蟄ｦ鄙貞腰蜈・ｸ隕ｧ縺瑚ｦ九▽縺九ｊ縺ｾ縺帙ｓ
      500:
        description: 繧ｵ繝ｼ繝舌・蜀・Κ繧ｨ繝ｩ繝ｼ
    """
    current_app.logger.info("learning_guest-API縺ｫ繧｢繧ｯ繧ｻ繧ｹ縺後≠繧翫∪縺励◆")

    try:
        level_id = request.args.get("level_id", type=int)
        language_id = request.args.get("language_id", type=int)

        if level_id is None or language_id is None:
            from apps.api.kotobaroots.models import Level

            if level_id is None:
                default_level = Level.query.order_by(Level.id).first()
                level_id = default_level.id if default_level else None

            if language_id is None:
                default_language = Language.query.order_by(Language.id).first()
                language_id = default_language.id if default_language else None

        if not level_id or not language_id:
            return jsonify({"msg": "蟄ｦ鄙定ｨｭ螳壹′隕九▽縺九ｊ縺ｾ縺帙ｓ"}), 404

        learning_topics = LearningTopic.query \
            .filter_by(level_id=level_id, language_id=language_id) \
            .order_by(LearningTopic.difficulty) \
            .all()

        if not learning_topics:
            return jsonify({"msg": "蟄ｦ鄙貞腰蜈・′隕九▽縺九ｊ縺ｾ縺帙ｓ"}), 404

        response_learning_topics = []
        for learning_topic in learning_topics:
            response_learning_topics.append({
                "id": learning_topic.id,
                "topic": learning_topic.topic,
                "difficulty": learning_topic.difficulty
            })

        return jsonify({
            "learning_topics": response_learning_topics,
            "current_max_difficulty": 1
        }), 200

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"msg": "繧ｨ繝ｩ繝ｼ縺檎匱逕溘＠縺ｾ縺励◆"}), 500