from datetime import datetime

from apps.extensions import db
# パスワードハッシュ化用
from werkzeug.security import generate_password_hash, check_password_hash

### リレーショナル関係


### User（ユーザー情報）
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, index=True)
    email = db.Column(db.String, nullable=False, unique=True, index=True)
    hashed_password = db.Column(db.String, nullable=False)
    
    # # ↓↓↓ JTI保存用のカラムを追加 (String型, nullable, index付き) ↓↓↓
    # refresh_token_jti = db.Column(db.String(36), nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    last_password_change = db.Column(db.DateTime, nullable=True)

    contacts = db.relationship("Contact", back_populates="user")
    learning_configs = db.relationship("LearningConfig", back_populates="user")
    myphrases_english = db.relationship("MyphraseEnglish", back_populates="user")
    myphrases_chinese = db.relationship("MyphraseChinese", back_populates="user")
    myphrases_korean = db.relationship("MyphraseKorean", back_populates="user")
    myphrases_french = db.relationship("MyphraseFrench", back_populates="user")
    ai_correction_histories = db.relationship("AICorrectionHistory", back_populates="user")

    @property
    def password(self):
        raise AttributeError("読み取り不可")
    
    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)

    # ログイン認証 (check_password_hash) のためのメソッドも追加
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

### ログアウトやハックされた場合などで無効化したリフレッシュトークンを保存しておくテーブル
class TokenBlocklist(db.Model):
    """
    無効化されたJWTトークンを保存するためのテーブル
    """
    __tablename__ = "token_blocklist"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # jti (JWT ID) は、トークンの一意な識別子です。
    # これをDBに保存して照合します。
    jti = db.Column(db.String(36), nullable=False, index=True, unique=True)
    
    # いつ無効化されたか（ログアウトしたか）の記録
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<Token {self.jti}>"