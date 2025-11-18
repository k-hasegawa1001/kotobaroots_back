import datetime
import logging
import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

### DB関連
from flask_migrate import Migrate
from .extensions import db
###

### メール関連
# 独立させた extensions と email をインポート
from .extensions import mail
###

### 認証関連(認証トークン)
# from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, JWTManager, set_refresh_cookies
from .extensions import jwt
from .api.auth.models import TokenBlocklist

###

### .env関連
from dotenv import load_dotenv

load_dotenv()
###

# ステージング環境切り替えのためファクトリ化
def create_app():
    app = Flask(__name__)

    ### 認証関連
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
    
    # リフレッシュトークンを保存するCookieの名前
    app.config["JWT_REFRESH_COOKIE_NAME"] = os.environ.get("JWT_REFRESH_COOKIE_NAME")
    
    # Cookieを安全にする設定 (HttpOnly)
    app.config["JWT_COOKIE_HTTPONLY"] = os.environ.get("JWT_COOKIE_HTTPONLY", "True").lower() == "true"
    app.config["JWT_COOKIE_SECURE"] = os.environ.get("JWT_COOKIE_SECURE", "False").lower() == "true"

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)

    # リフレッシュトークンの有効期限を30日に設定 (Cookieに反映されます)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=30)
    
    app.config["JWT_ENABLE_BLOCKLIST"] = True
    app.config["JWT_BLOCKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

    # jwt = JWTManager(app)
    jwt.init_app(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token_in_db = TokenBlocklist.query.filter_by(jti=jti).one_or_none()
        return token_in_db is not None
    ###

    app.config["JSON_AS_ASCII"] = False
    app.logger.setLevel(logging.DEBUG)

    CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5500"])

    ### DB関連
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # SQLAlchemyとアプリの連携する
    db.init_app(app)
    # Migrateとアプリを連携する
    Migrate(app, db)

    from apps.api.auth import models
    from apps.api.kotobaroots import models
    ###

    ### メール関連
    # メールコンフィグ
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT"))
    app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
    app.config["MAIL_DEBUG"] = True # デバッグが終わったらFalseにする

    # 拡張機能の「初期化」
    # extensions.py からインポートした mail オブジェクトを、ここで app と紐付ける
    mail.init_app(app)
    ###
    
    # authパッケージimport
    from apps.api.auth import auth_api

    app.register_blueprint(auth_api.api, url_prefix="/api/auth")

    return app
