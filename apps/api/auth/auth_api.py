import datetime
# import logging

from flask import Blueprint, request, render_template, current_app, jsonify

# メール
from ...email import send_email

from flask_jwt_extended import create_access_token, create_refresh_token, get_jti, set_refresh_cookies

# DB関連
from apps.api.auth.models import User
from apps.app import db

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

        return f"Hello, {email}!"
    else:
        return "Hello, Guest!"

### ログイン
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

        # メールアドレスが登録されていなかった場合
        if user == None:
            response = jsonify({"msg": "メールアドレスかパスワードが間違っています"})
            return response, 200

        # passwordが合っているかの確認（check_password）
        if user.check_password(password):
            # passwordが正しい場合
            # print('パスワード合ってる')
            user_identity = user.id
            # 1. アクセストークンを生成 (有効期限: 15分)
            access_token = create_access_token(identity=user_identity)
    
            # 2. リフレッシュトークンを生成 (有効期限: 30日)
            refresh_token = create_refresh_token(identity=user_identity)

            """
            response.body(json)
            {
                "access_token": "...",
                "user_info": "..."
            }
            """
            response_body = {
                "access_token": access_token,
                "user_info":{"username": user.username, "email": email}
            }
            response = jsonify(response_body)

            # リフレッシュトークンを HttpOnly Cookie に設定
            # max_ageは設定（JWT_REFRESH_TOKEN_EXPIRES）から自動で読み込まれる
            set_refresh_cookies(response, refresh_token)

            return response, 200
        else:
            # パスワードが間違っている場合
            # print('パスワード間違い')
            response = jsonify({"msg": "メールアドレスかパスワードが間違っています"})
            return response, 200
        
        ############# user != nullなら、ここで2要素認証としてメールを送信する
        
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500

### 二要素認証（余裕があったらあとで実装する）
# @api.route("/verify-2fa/<email>")
# def verify_2fa():
#     print()

### リフレッシュトークンからアクセストークンを生成するAPI
@api.route("/token/refresh")
def generate_access_token_from_refresh_token():
    print()

### 新規登録
@api.route("/create_user", methods=["POST"])
def create_user():
    current_app.logger.info("create_user-APIにアクセスがありました")
    """
    request.body(json)
    {
        "username": "...",
        "email": "...",
        "password": "..."
    }
    """
    try:
        create_user_data = request.get_json()
        username = create_user_data.get("username")
        email = create_user_data.get("email")
        password = create_user_data.get("password")

        ### セキュリティ面考慮（後で実装）
        ###

        new_user = User(username=username, email=email)
        new_user.password=password # ここでハッシュ化が呼び出されてるはず

        db.session.add(new_user)
        db.session.commit()

        response_body={
            "msg": "アカウント作成完了"
        }

        response = jsonify(response_body)

        return response, 200

    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"error": str(e)}), 500