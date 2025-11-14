import logging
import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

### DB関連
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemyをインスタンス化
db = SQLAlchemy()
###

### メール関連
# 独立させた extensions と email をインポート
from .extensions import mail
###

### .env関連
from dotenv import load_dotenv

load_dotenv()
###

# ステージング環境切り替えのためファクトリ化
def create_app():
    app = Flask(__name__)

    app.config["JSON_AS_ASCII"] = False
    app.logger.setLevel(logging.DEBUG)

    CORS(app)

    ### DB関連
    app.config.from_mapping(
        SECRET_KEY="2AZSMss3p5QPBcY2hBsJ",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # SQLAlchemyとアプリの連携する
    db.init_app(app)
    # Migrateとアプリを連携する
    Migrate(app, db)
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
