from datetime import datetime

from apps.extensions import db
from sqlalchemy import UniqueConstraint

### Contact（問い合わせ）
class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String, nullable=False)

    user = db.relationship("User", back_populates="contacts")

### Level（学習レベル）
class Level(db.Model):
    __tablename__ = "levels"

    id = db.Column(db.Integer, primary_key=True)
    level_tag = db.Column(db.String, nullable=False)

    learning_configs = db.relationship("LearningConfig", backref="level")
    learning_topics = db.relationship("LearningTopic", back_populates="level", order_by="LearningTopic.difficulty")
    unlocked_topics = db.relationship("UnlockedTopic", back_populates="level")

### Language（学習言語・国）
class Language(db.Model):
    __tablename__ = "languages"
    
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String, nullable=False)
    country = db.Column(db.String, nullable=True)

    learning_configs = db.relationship("LearningConfig", backref="language")
    learning_topics = db.relationship("LearningTopic", back_populates="language")

### LearningConfig（学習設定）
class LearningConfig(db.Model):
    __tablename__ = "learning_configs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=False)
    myphrase_question_num = db.Column(db.Integer, default=100, nullable=False)
    is_applying = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="learning_configs")

### myphrase_○○（マイフレーズ帳）
# 英語
class MyphraseEnglish(db.Model):
    __tablename__ = "myphrases_english"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phrase = db.Column(db.String, nullable = False)
    mean = db.Column(db.String, nullable = False)

    user = db.relationship("User", back_populates="myphrases_english")

# 中国語
class MyphraseChinese(db.Model):
    __tablename__ = "myphrases_chinese"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phrase = db.Column(db.String, nullable = False)
    mean = db.Column(db.String, nullable = False)

    user = db.relationship("User", back_populates="myphrases_chinese")

# 韓国語
class MyphraseKorean(db.Model):
    __tablename__ = "myphrases_korean"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phrase = db.Column(db.String, nullable = False)
    mean = db.Column(db.String, nullable = False)

    user = db.relationship("User", back_populates="myphrases_korean")

# フランス語
class MyphraseFrench(db.Model):
    __tablename__ = "myphrases_french"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phrase = db.Column(db.String, nullable = False)
    mean = db.Column(db.String, nullable = False)

    user = db.relationship("User", back_populates="myphrases_french")

### AI解説履歴
class AICorrectionHistory(db.Model):
    __tablename__ = "ai_correction_histories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=False)
    # 長文になる可能性があるのでString型ではなくText型を使用
    input_english = db.Column(db.Text, nullable = False)
    japanese_translation = db.Column(db.Text, nullable = False)
    explanation = db.Column(db.Text, nullable = False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    user = db.relationship("User", back_populates="ai_correction_histories")

### 学習
## 学習単元
class LearningTopic(db.Model):
    __tablename__ = "learning_topics"

    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=False)
    topic = db.Column(db.String, nullable = False)
    difficulty = db.Column(db.Integer, nullable = False)

    __table_args__ = (
        UniqueConstraint('language_id', 'level_id', 'difficulty', name='unique_lang_level_difficulty'),
    )

    level = db.relationship("Level", back_populates="learning_topics")
    language = db.relationship("Language", back_populates="learning_topics")
    unlocked_topics = db.relationship("UnlockedTopic", back_populates="learning_topic")

## アンロック単元
class UnlockedTopic(db.Model):
    __tablename__ = "unlocked_topics"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    learning_topic_id = db.Column(db.Integer, db.ForeignKey('learning_topics.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'learning_topic_id', name='unique_user_topic_unlock'),
    )

    user = db.relationship("User", back_populates="unlocked_topics")
    level = db.relationship("Level", back_populates="unlocked_topics")
    learning_topic = db.relationship("LearningTopic", back_populates="unlocked_topics")