import sys
import os
from werkzeug.security import generate_password_hash

# プロジェクトのルートパスをPythonの検索パスに追加
sys.path.append(os.getcwd())

from apps.app import create_app
from apps.extensions import db

# ---------------------------------------------------------
# モデルのインポート（ディレクトリ修正）
# ---------------------------------------------------------
# Auth関連: apps/api/auth/models.py
from apps.api.auth.models import User 

# API/学習関連: apps/api/kotobaroots/models.py
from apps.api.kotobaroots.models import Language, Level, LearningTopic, LearningConfig

app = create_app()

def seed_data():
    """初期データの投入（パス修正版）"""
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
        test_password = "password" 

        user = User.query.filter_by(email=test_email).first()
        if not user:
            user = User(
                username=test_username,
                email=test_email,
                password=test_password 
            )
            db.session.add(user)
            print(f"   [User] Created: {test_username} (pass: {test_password})")
        else:
            print(f"   [User] Exists: {test_username}")
        
        db.session.flush()

        # Config作成
        if user.id:
            config = LearningConfig.query.filter_by(user_id=user.id).first()
            if not config:
                config = LearningConfig(
                    user_id=user.id,
                    level_id=levels["Beginner"].id,
                    language_id=langs["English_America"].id,
                    myphrase_question_num=10,
                )
                db.session.add(config)
                print("   [Config] Created default config for testuser")

        # ---------------------------------------------------------
        # 4. LearningTopic（学習単元）の作成
        # ---------------------------------------------------------
        
        topics_map = {
            "Beginner": { # 初級
                "アルファベット": "alphabet",
                "基本語彙": "basic_vocabulary",
                "be動詞": "be_verb",
                "一般動詞": "general_verb",
                "否定文": "negative_form",
                "疑問文": "interrogative_form",
                "助動詞": "auxiliary_verb",
                "疑問詞": "question_word",
                "複数形": "plural_form",
                "三人称単数": "third_person_singular",
                "人称代名詞": "personal_pronoun",
                "現在進行形": "present_progressive",
                "過去形": "past_tense",
                "過去進行形": "past_progressive",
                "未来表現": "future_tense",
                "接続詞": "conjunction",
                "不定詞": "infinitive",
                "動名詞": "gerund",
                "比較": "comparison",
                "受動態": "passive_voice",
                "現在完了形": "present_perfect",
                "分詞": "participle",
                "関係代名詞": "relative_pronoun",
                "間接疑問文": "indirect_question",
                "仮定法": "subjunctive_mood"
            },
            "Intermediate": { # 中級
                "文型": "sentence_pattern",
                "完了進行形": "perfect_progressive",
                "未来完了": "future_perfect",
                "助動詞(応用)": "advanced_auxiliary",
                "群動詞の受動態": "phrasal_verb_passive",
                "意味上の主語": "logical_subject",
                "完了不定詞": "perfect_infinitive",
                "分詞構文": "participle_construction",
                "関係副詞": "relative_adverb",
                "複合関係詞": "compound_relative",
                "非制限用法": "non_restrictive_usage",
                "仮定法過去": "subjunctive_past",
                "仮定法過去完了": "subjunctive_past_perfect",
                "無生物主語": "inanimate_subject",
                "強調構文": "cleft_sentence",
                "倒置": "inversion",
                "省略": "ellipsis",
                "同格": "apposition"
            },
            "Advanced": { # 上級
                "米英豪の差異": "regional_varieties",
                "聖書・神話由来": "biblical_mythological",
                "文学・古典由来": "literary_references",
                "歴史的メタファー": "historical_metaphors",
                "婉曲表現": "euphemism",
                "包括的表現(PC)": "inclusive_language",
                "皮肉・ユーモア": "sarcasm_irony",
                "フォーマル・品格": "register_formal",
                "世代別スラング": "generational_slang",
                "ネットスラング": "internet_slang",
                "ポップカルチャー": "pop_culture_quotes"
            }
        }

        target_lang = langs["English_America"]

        for level_tag, topics_dict in topics_map.items():
            target_level = levels[level_tag]
            difficulty_counter = 1
            
            print(f"\n--- Processing {level_tag} Topics ---")
            
            for title, key in topics_dict.items():
                topic = LearningTopic.query.filter_by(
                    language_id=target_lang.id,
                    level_id=target_level.id,
                    topic_key=key 
                ).first()

                if not topic:
                    topic = LearningTopic(
                        language_id=target_lang.id,
                        level_id=target_level.id,
                        topic=title,
                        topic_key=key,
                        difficulty=difficulty_counter
                    )
                    db.session.add(topic)
                    print(f"   [Topic] Created: {title} ({key}) - Diff:{difficulty_counter}")
                else:
                    updated = False
                    if topic.difficulty != difficulty_counter:
                        topic.difficulty = difficulty_counter
                        updated = True
                    if topic.topic != title:
                        topic.topic = title
                        updated = True
                    
                    if updated:
                        print(f"   [Topic] Updated: {title} ({key}) - Diff:{difficulty_counter}")
                    else:
                        print(f"   [Topic] Exists: {title}")

                difficulty_counter += 1

        try:
            db.session.commit()
            print("\n✨ 全データの投入が完了しました！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    seed_data()