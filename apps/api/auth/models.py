from datetime import datetime

from apps.app import db
# パスワードハッシュ化用
from werkzeug.security import generate_password_hash, check_password_hash

### User（完成）
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, index=True)
    email = db.Column(db.String, nullable=False, unique=True, index=True)
    hashed_password = db.Column(db.String, nullable=False)
    
    # ↓↓↓ JTI保存用のカラムを追加 (String型, nullable, index付き) ↓↓↓
    refresh_token_jti = db.Column(db.String(36), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    @property
    def password(self):
        raise AttributeError("読み取り不可")
    
    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    # ログイン認証 (check_password_hash) のためのメソッドも追加
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)