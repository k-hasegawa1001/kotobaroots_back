import datetime
# import logging

from flask import Blueprint, request, render_template, current_app, jsonify

# メール
from ...email import send_email

# 認証
from flask_login import login_user, logout_user, login_required, current_user

# from flask_jwt_extended import create_access_token, create_refresh_token, get_jti, set_refresh_cookies, jwt_required, get_jwt_identity, get_jwt, unset_jwt_cookies

# DB関連
from apps.extensions import db
from apps.api.auth.models import User
from apps.api.kotobaroots.models import LearningConfig

# リフレッシュトークン無効化用
# from .models import TokenBlocklist

# パスワードリセット用
from itsdangerous import URLSafeTimedSerializer # メールに添付するURLに改ざん検知のトークンを付与するためのもの
from .utils import generate_reset_token, verify_reset_token

api = Blueprint(
    "auth",
    __name__
)

# api.logger.setLevel(logging.DEBUG)

# @api.route("/", methods=["GET", "POST"])
# def index():
#     current_app.logger.warning(f"【warning!!!!!】不正なアクセスが行われようとした形跡があります")
    
#     if request.method == "POST":
#         email = request.form["email"]

#         # # メール送信テスト（デバッグ用）
#         send_email(email,"test","/test_mail",admin_name="名無しの専門学生")
#         # #

#         return f"Hello, {email}!"
#     else:
#         return "Hello, Guest!"

### ログイン（長谷川）(http://127.0.0.1:5000/api/auth/login)
@api.route("/login", methods=["POST"])
def login():
    """
    ユーザーログインAPI (Flask-Login)

    メールアドレスとパスワードで認証を行います。
    成功するとサーバー側でセッションを作成し、ブラウザのCookieにセッションIDを保存します。
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        description: ログイン情報
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: "test@example.com"
              description: 登録済みのメールアドレス
            password:
              type: string
              example: "password123"
              description: 登録済みのパスワード
    responses:
      200:
        description: ログイン成功（Cookieにセッション情報が設定されます）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Login successful"
              description: 成功メッセージ
            user_info:
              type: object
              description: ユーザー情報
              properties:
                username:
                  type: string
                  example: "テストユーザー"
                email:
                  type: string
                  example: "test@example.com"
      401:
        description: 認証失敗（メールアドレスまたはパスワードの誤り）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "メールアドレスかパスワードが間違っています"
      500:
        description: サーバー内部エラー
        schema:
          properties:
            error:
              type: string
    """
    current_app.logger.info("login-APIにアクセスがありました")
    
    try:
        login_data = request.get_json()
        email = login_data.get("email")
        password = login_data.get("password")

        user = User.query.filter_by(email=email).first()

        # メールアドレスが登録されていなかった場合
        if user == None:
            response = jsonify({"msg": "メールアドレスかパスワードが間違っています"})
            return response, 401

        # passwordが合っているかの確認（check_password）
        if user.check_password(password):
            # passwordが正しい場合
            # print('パスワード合ってる')
            # user_identity = user.id
            # # 1. アクセストークンを生成 (有効期限: 15分)
            # access_token = create_access_token(identity=user_identity)
    
            # # 2. リフレッシュトークンを生成 (有効期限: 30日)
            # refresh_token = create_refresh_token(identity=user_identity)

            # """
            # response.body(json)
            # {
            #     "access_token": "...",
            #     "user_info": "..."
            # }
            # """
            # response_body = {
            #     "access_token": access_token,
            #     "user_info":{"username": user.username, "email": email}
            # }
            # response = jsonify(response_body)

            # # リフレッシュトークンを HttpOnly Cookie に設定
            # # max_ageは設定（JWT_REFRESH_TOKEN_EXPIRES）から自動で読み込まれる
            # set_refresh_cookies(response, refresh_token)

            login_user(user, remember=True)

            response_body = {
              "msg": "Login successful",
              "user_info": {"username": user.username, "email": email}
            }
            response = jsonify(response_body)

            return response, 200
        else:
            # パスワードが間違っている場合
            # print('パスワード間違い')
            response = jsonify({"msg": "メールアドレスかパスワードが間違っています"})
            return response, 401
        
        ############# user != nullなら、ここで2要素認証としてメールを送信する
        
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

### 二要素認証（余裕があったらあとで実装する）
# @api.route("/verify-2fa/<email>")
# def verify_2fa():
#     print()

# ## トークン検証（長谷川）
# # http://127.0.0.1:5000/api/auth/reset-password/confirm-token/<token>
# @api.route("/reset-password/confirm-token/<token>", methods=["GET"])
# def confirm_reset_password_token(token):
#     """
#     フロントエンドが画面を表示する前に、「このトークン生きてる？」を確認するためのAPI
#     """
#     email = verify_reset_token(token)
    
#     if not email:
#         return jsonify({"msg": "無効、または期限切れのリンクです"}), 400

#     # 問題なければ、変更しようとしているメアドなどを返す（画面表示用）
#     return jsonify({
#         "msg": "トークンは有効です"
#     }), 200

# ### リフレッシュトークンからアクセストークンを生成するAPI（長谷川）
# # http://127.0.0.1:5000/api/auth/token/refresh
# @api.route("/token/refresh")
# @jwt_required(refresh=True)
# def generate_access_token_from_refresh_token():
#     """
#     アクセストークン再発行API
    
#     Cookieに保存された有効なリフレッシュトークンを使用して、
#     新しいアクセストークンを発行します。
#     ---
#     tags:
#       - Auth
#     responses:
#       200:
#         description: 成功（新しいアクセストークンの発行）
#         schema:
#           type: object
#           properties:
#             access_token:
#               type: string
#               description: 新しいアクセストークン
#               example: "eyJ0eXAiOiJKV1QiLCJhbG..."
#       401:
#         description: 認証エラー（リフレッシュトークンが無効、期限切れ、またはCookieに存在しない）
#       500:
#         description: サーバー内部エラー
#     """
#     current_user_identity = get_jwt_identity()
#     new_access_token = create_access_token(identity=current_user_identity)
#     return jsonify(access_token=new_access_token), 200

### ログアウトAPI（長谷川）
# http://127.0.0.1:5000/api/auth/logout
@api.route("/logout", methods=["POST"])
# @jwt_required(refresh=True) # リフレッシュトークンでログアウトするのが一般的
@login_required
def logout():
    """
    ログアウトAPI (Flask-Login)
    
    現在ログインしているユーザーのセッションをサーバー側で破棄し、ログアウト状態にします。
    実行にはログイン状態（有効なセッションCookie）が必要です。
    ---
    tags:
      - Auth
    responses:
      200:
        description: ログアウト成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "Successfully logged out"
      401:
        description: 認証エラー（ログインしていない状態でアクセスした場合）
      500:
        description: サーバー内部エラー
        schema:
          properties:
            msg:
              type: string
            error:
              type: string
    """
    
    try:
        # # 現在のリクエストで使われているトークンの 'jti' を取得
        # jti = get_jwt()["jti"]
        
        # # 新しい TokenBlocklist レコードを作成
        # blocklist_entry = TokenBlocklist(jti=jti)
        
        # # DBセッションに追加してコミット
        # db.session.add(blocklist_entry)
        # db.session.commit()
        logout_user()
        
        res_body = {"msg": "Successfully logged out"}
        response = jsonify(res_body)
        # unset_jwt_cookies(response)

        return response, 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error processing logout", "error": str(e)}), 500

### 新規登録（長谷川）
# ここで学習設定情報も作成
# http://127.0.0.1:5000/api/auth/create-user
@api.route("/create-user", methods=["POST"])
def create_user():
    """
    ユーザー新規登録API
    
    ユーザーアカウントを作成し、同時にデフォルトの学習設定（レベル1、英語など）を初期化します。
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        description: 新規登録情報
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: "新規ユーザー"
              description: 表示名
            email:
              type: string
              example: "new_user@example.com"
              description: メールアドレス
            password:
              type: string
              example: "password123"
              description: パスワード
    responses:
      200:
        description: 作成成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "アカウント作成完了"
      500:
        description: サーバー内部エラー（メールアドレスの重複登録など）
        schema:
          type: object
          properties:
            error:
              type: string
    """
    current_app.logger.info("create_user-APIにアクセスがありました")
    
    try:
        create_user_data = request.get_json()
        username = create_user_data.get("username")
        email = create_user_data.get("email")
        password = create_user_data.get("password")

        ### セキュリティ面考慮（後で実装）
        ###

        new_user = User(username=username, email=email)
        new_user.password=password # これでハッシュ化が実行される

        # db.session.add(new_user)
        # # db.session.commit()
        # db.session.flush() # flush()を使うことでコミットはされないが、user_idが発行されnew_usr.idにセットされる

        # ここでlearning_configも設定
        """
        learning_configの初期値
        level_id=1（初級）
        language_id=1（英語、アメリカ）
        myphrase_question_num=100（全問）
        (is_applyingは廃止のため設定不要)
        """
        new_config = LearningConfig(
            level_id=1,
            language_id=1,
            myphrase_question_num=100
        )

        # new_user.learning_configs.append(new_config)
        # 【変更点】
        # 1対1 (uselist=False) にしたため、append() ではなく直接代入します
        # 変数名も models.py に合わせて learning_config (単数) にしています
        new_user.learning_config = new_config

        db.session.add(new_user)

        # db.session.add(new_learning_config)
        db.session.commit()

        response_body={
            "msg": "アカウント作成完了"
        }

        response = jsonify(response_body)

        return response, 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

### パスワードリセット
## メール送信（長谷川）
# http://127.0.0.1:5000/api/auth/request-reset-password
@api.route("/request-reset-password", methods=["POST"])
def request_password_reset():
    """
    パスワードリセットリクエストAPI
    
    指定されたメールアドレス宛に、パスワード再設定用のURL（トークン付き）を記載したメールを送信します。
    
    【セキュリティ仕様】
    アカウント列挙攻撃を防ぐため、未登録のメールアドレスが送信された場合でも、
    エラーにはせず「送信しました」という成功レスポンス（200 OK）を返します。
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        description: リセットしたいアカウントのメールアドレス
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: "forgot_user@example.com"
              description: 登録済みのメールアドレス
    responses:
      200:
        description: 受付完了（メール送信成功、または未登録アドレスに対するダミー応答）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "パスワードリセットメールを送信しました"
      500:
        description: サーバー内部エラー（メールサーバーの不調など）
        schema:
          type: object
          properties:
            error:
              type: string
    """
    current_app.logger.info("request_password_reset-APIにアクセスがありました")
    
    try:
        req_data = request.get_json()
        email = req_data.get("email")

        user = User.query.filter_by(email=email).first()

        # セキュリティのため、登録がない場合でも「送信しました」と返す
        if not user:
            current_app.logger.info("ユーザー情報が存在していませんでした")
            return jsonify({"msg": "パスワードリセットメールを送信しました"}), 200


        ## TODO: 24時間以内にもう一度パスワードリセットリクエストが来た場合の処理を後で考える
        # レートリミット（Flask-Limiterなど）か専用のメールテンプレートを使用

        token = generate_reset_token(user.email)

        frontend_url = current_app.config.get("FRONTEND_URL", "http://127.0.0.1:5500")

        reset_url = f"{frontend_url}/reset-password.html?token={token}"

        email_template = "/password_reset/password_reset"

        send_email(user.email, "パスワードリセット", email_template, reset_url=reset_url)
        
        return jsonify({"msg": "パスワードリセットメールを送信しました"}), 200
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": "エラーが発生しました"}), 500

## パスワードリセット処理（長谷川）
# http://127.0.0.1:5000/api/auth/reset-password
@api.route("/reset-password", methods=["POST"])
def reset_password():
    """
    パスワードリセット実行API
    
    メールで受け取ったトークンと新しいパスワードを送信し、パスワードの変更を完了させます。
    トークンの有効期限切れや改ざんが検知された場合は400エラーを返します。
    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        description: リセット情報
        schema:
          type: object
          required:
            - token
            - password
          properties:
            token:
              type: string
              description: メールに記載された認証用トークン
              example: "IjU..."
            password:
              type: string
              description: 新しいパスワード
              example: "new_password123"
    responses:
      200:
        description: 変更成功
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "パスワードが正常に変更されました"
      400:
        description: リクエスト不正（情報不足、またはトークンの無効・期限切れ）
        schema:
          type: object
          properties:
            msg:
              type: string
              example: "無効、または期限切れのリンクです"
      404:
        description: ユーザー不明（トークンは正しいが対象ユーザーがDBにいない場合など）
      500:
        description: サーバー内部エラー
        schema:
          type: object
          properties:
            error:
              type: string
    """
    current_app.logger.info("reset-password-APIにアクセスがありました")
    
    try:
        req_data = request.get_json()
        token = req_data.get("token")
        new_password = req_data.get("password")

        if not token or not new_password:
            return jsonify({"msg": "情報が不足しています"}), 400

        # トークンの検証
        email = verify_reset_token(token)

        if not email:
            return jsonify({"msg": "無効、または期限切れのリンクです"}), 400

        # ユーザーを取得してパスワード更新
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"msg": "ユーザーが見つかりません"}), 404
        
        # パスワードのsetterメソッドでハッシュ化して保存
        user.password = new_password
        user.last_password_change = datetime.datetime.utcnow()
        db.session.commit()

        return jsonify({"msg": "パスワードが正常に変更されました"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500