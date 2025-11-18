from apps.extensions import db

### Contact（問い合わせ）
class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String, nullable=False)

### Level（学習レベル）
class Level(db.Model):
    __tablename__ = "levels"
    
    id = db.Column(db.Integer, primary_key=True)
    level_tag = db.Column(db.String, nullable=False)
