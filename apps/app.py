import logging
import os

from flask import Flask
from flask_cors import CORS

from dotenv import load_dotenv

load_dotenv()

# 独立させた extensions と email をインポート
from .extensions import mail
from .email import send_email  # authentication_at_email_address で使うならインポート

# ステージング環境切り替えのためファクトリ化
def create_app():
    app = Flask(__name__)

    app.config["JSON_AS_ASCII"] = False
    app.logger.setLevel(logging.DEBUG)

    CORS(app)

    ### メール機能
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
    from apps.auth import auth_api

    app.register_blueprint(auth_api.api, url_prefix="/auth")

    return app
