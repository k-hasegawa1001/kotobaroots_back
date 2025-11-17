from flask_mail import Mail

from flask_sqlalchemy import SQLAlchemy

# 認証関連
from flask_jwt_extended import JWTManager

# app.py内でapp（Flask(__name__)）と結びつける
mail = Mail()

db = SQLAlchemy()

jwt = JWTManager()

