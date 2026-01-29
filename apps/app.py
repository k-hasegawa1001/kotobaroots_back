# import datetime
import logging
import os
from pathlib import Path

from flask import Flask, request
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
# from .extensions import jwt
# from .api.auth.models import TokenBlocklist
from apps.api.auth.models import User
from .extensions import login_manager
###

### .env関連
from dotenv import load_dotenv

load_dotenv()
###

### API仕様書関連
from flasgger import Swagger
###

### 学習履歴削除のためのバッチ関連
import click
from datetime import datetime, timedelta
###

# ステージング環境切り替えのためファクトリ化
def create_app():
    app = Flask(__name__)

    # ### メールに添付するURLのトークン関連
    # app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

    ### chatGPT-API
    app.config["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")

    ### 認証関連
    
    ###

    app.config["JSON_AS_ASCII"] = False
    app.logger.setLevel(logging.DEBUG)

    # frontend_url = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5500")
    # app.config["FRONTEND_URL"] = frontend_url
    # # CORS(app, supports_credentials=True, origins=[frontend_url])
    # CORS(app,
    #     resources={r"/api/*": {
    #         "origins": [frontend_url],
    #         "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    #         "allow_headers": ["Content-Type", "Authorization"],
    #         "supports_credentials": True
    #     }}
    # )
    
    # .envの設定値(5500)に加え、LiveServerが5501になった場合も許可するリストを作成
    frontend_base = os.environ.get("FRONTEND_URL", "http://127.0.0.1:5500")
    allowed_origins = [frontend_base, "http://127.0.0.1:5501"]

    app.config["FRONTEND_URL"] = frontend_base # configにはメインの方を入れておく

    CORS(app,
        resources={r"/api/*": {
            "origins": allowed_origins, # ← リストを渡すことで複数許可されます
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }}
    )

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

    ### API仕様書関連
    swagger = Swagger(app)
    ###

    ### 認証関連
    login_manager.init_app(app)

    # 1. ユーザー読み込み関数 (セッションIDからユーザーを復元)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 2. 未認証時のハンドラ (API向けに重要！)
    # ログインしていない状態でアクセスがあった場合、勝手にリダイレクトせず
    # 明確に 401 エラーを返すようにします。
    @login_manager.unauthorized_handler
    def unauthorized():
        return {"msg": "ログインが必要です"}, 401
    ###
    
    # authパッケージimport
    from apps.api.auth import auth_api

    app.register_blueprint(auth_api.api, url_prefix="/api/auth")

    # kotobarootsパッケージインポート
    from apps.api.kotobaroots import kotobaroots_api

    app.register_blueprint(kotobaroots_api.api, url_prefix="/api/kotobaroots")

    # ---------------------------------------------------------
    # 【追加】 バッチ処理用コマンドの登録
    # ---------------------------------------------------------
    @app.cli.command("cleanup-history")
    def cleanup_history():
        """3ヶ月以上前の学習履歴を物理削除するコマンド"""
        # ここでインポートすることで循環参照を回避
        from apps.api.kotobaroots.models import LearningHistory
        
        # 3ヶ月前（90日前）の日時を計算
        threshold_date = datetime.now() - timedelta(days=90)
        
        print(f"[{datetime.now()}] クリーンアップ開始: {threshold_date} 以前のデータを削除します...")

        try:
            # 削除実行
            # FlaskのCLI経由で実行されるため、自動的にアプリコンテキスト(dbセッション等)が有効になっています
            deleted_count = LearningHistory.query.filter(
                LearningHistory.created_at < threshold_date
            ).delete()
            
            db.session.commit()
            print(f"[{datetime.now()}] 完了: {deleted_count}件の古い履歴を削除しました。")
        except Exception as e:
            db.session.rollback()
            print(f"[{datetime.now()}] エラー発生: {e}")

    return app
