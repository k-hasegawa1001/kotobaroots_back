import sys
import os

# プロジェクトのルートパスをPythonの検索パスに追加
sys.path.append(os.getcwd())

from apps.app import create_app
from apps.extensions import db

# ---------------------------------------------------------
# モデルのインポート（パスを修正）
# ---------------------------------------------------------
# Auth関連
from apps.api.auth.models import User 
# API/学習関連
from apps.api.kotobaroots.models import Language, Level, LearningTopic, LearningConfig

app = create_app()

def seed_data():
    """初期データの投入（Userモデル対応版）"""
    with app.app_context():
        print("🌱 データの投入を開始します...")

        # ---------------------------------------------------------
        # 1. Level（学習レベル）の作成
        # ---------------------------------------------------------
        levels_data = ["Beginner", "Intermediate", "Advanced"]
        levels = {} 

        for tag in levels_data:
            level = Level.query.filter_by(level_tag=tag).first()
            if not level:
                level = Level(level_tag=tag)
                db.session.add(level)
                print(f"   [Level] Created: {tag}")
            else:
                print(f"   [Level] Exists: {tag}")
            levels[tag] = level
        
        db.session.flush()

        # ---------------------------------------------------------
        # 2. Language（言語・国）の作成
        # ---------------------------------------------------------
        languages_data = [
            ("English", "America"),
            ("English", "UK"),
            ("Chinese", "China"),
        ]
        langs = {}

        for lang_name, country in languages_data:
            lang = Language.query.filter_by(language=lang_name, country=country).first()
            if not lang:
                lang = Language(language=lang_name, country=country)
                db.session.add(lang)
                print(f"   [Language] Created: {lang_name} ({country})")
            else:
                print(f"   [Language] Exists: {lang_name} ({country})")
            
            key = f"{lang_name}_{country}"
            langs[key] = lang

        db.session.flush()

        # ---------------------------------------------------------
        # 3. User（テストユーザー）の作成
        # ---------------------------------------------------------
        test_username = "testuser"
        test_email = "test@example.com"
        test_password = "password" # ログイン用パスワード

        user = User.query.filter_by(email=test_email).first()
        if not user:
            # Userモデルの @password.setter を利用してハッシュ化
            user = User(
                username=test_username,
                email=test_email,
                password=test_password  # ここで自動的に hashed_password に変換されます
            )
            db.session.add(user)
            print(f"   [User] Created: {test_username} (pass: {test_password})")
        else:
            print(f"   [User] Exists: {test_username}")
        
        db.session.flush()

        # ---------------------------------------------------------
        # 4. LearningConfig（ユーザー設定）の作成
        # ---------------------------------------------------------
        # アプリ起動時に設定がないとエラーになる可能性があるため、デフォルト設定を作成
        if user.id: # userが正しく作成されていれば
            config = LearningConfig.query.filter_by(user_id=user.id).first()
            if not config:
                config = LearningConfig(
                    user_id=user.id,
                    level_id=levels["Beginner"].id,
                    language_id=langs["English_America"].id,
                    myphrase_question_num=10,
                    is_applying=True
                )
                db.session.add(config)
                print("   [Config] Created default config for testuser")

        # ---------------------------------------------------------
        # 5. LearningTopic（学習単元）の作成
        # ---------------------------------------------------------
        target_lang = langs["English_America"]
        target_level = levels["Beginner"]

        # (日本語タイトル, 英語ファイルキー, 難易度順序)
        topics_data = [
            ("be動詞", "be_verb", 1),
            ("一般動詞", "general_verb", 2),
            ("現在進行形", "present_progressive", 3),
            ("過去形", "past_tense", 4),
            ("未来形", "future_tense", 5),
            ("仮定法", "subjunctive_mood", 10),
        ]

        for title, key, difficulty in topics_data:
            topic = LearningTopic.query.filter_by(
                language_id=target_lang.id,
                level_id=target_level.id,
                difficulty=difficulty
            ).first()

            if not topic:
                topic = LearningTopic(
                    language_id=target_lang.id,
                    level_id=target_level.id,
                    topic=title,
                    topic_key=key,
                    difficulty=difficulty
                )
                db.session.add(topic)
                print(f"   [Topic] Created: {title} ({key})")
            else:
                if topic.topic_key != key:
                    topic.topic_key = key
                    print(f"   [Topic] Updated Key: {title} -> {key}")
                else:
                    print(f"   [Topic] Exists: {title}")

        # ---------------------------------------------------------
        # 保存
        # ---------------------------------------------------------
        try:
            db.session.commit()
            print("✨ 全データの投入が完了しました！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    seed_data()