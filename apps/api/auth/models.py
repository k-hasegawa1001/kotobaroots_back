from datetime import datetime

from apps.app import db
# パスワードハッシュ化用
from werkzeug.security import generate_password_hash

### User
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    hashed_password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.Date, nullable=False, default=datetime.now)
    updated_at = db.Column(db.Datetime, onupdate=datetime.now)

    @property
    def password(self):
        raise AttributeError("読み取り不可")
    
    @password.setter
    def password(self, password):
        self.hashed_password = generate_password_hash(password)
