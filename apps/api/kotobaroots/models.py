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

    learning_configs = db.relationship("LearningConfig", backref="level")

### Language（学習言語・国）
class Language(db.Model):
    __tablename__ = "languages"
    
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=True)

    learning_configs = db.relationship("LearningConfig", backref="language")

### LearningConfig（学習設定）
class LearningConfig(db.Model):
    __tablename__ = "learning_configs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=False)
    myphrase_question_num = db.Column(db.Integer, default=100, nullable=False)
