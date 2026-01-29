# seed_topics.py

from apps.app import create_app
from apps.extensions import db
from apps.api.kotobaroots.models import LearningTopic
from sqlalchemy import func

# アプリケーションコンテキストを作成
app = create_app()

def get_next_difficulty(level_id):
    """指定されたレベルの次のdifficulty（難易度順）を自動計算する"""
    max_diff = db.session.query(func.max(LearningTopic.difficulty))\
        .filter_by(level_id=level_id)\
        .scalar()
    return 1 if max_diff is None else max_diff + 1

def add_topics():
    # ここに登録したいデータをリストで書く
    # difficultyは書かなくてOK（自動計算される）
    topics_data = [
        # --- レベル1 (初級) ---
        """
        example
        {"lang": english, "level_id": 1, "topic": "Basic Greetings"},
        {"lang": english, "level_id": 1, "topic": "Self Introduction"},
        {"lang": english, "level_id": 1, "topic": "Numbers & Time"},
        """
        
        # --- レベル2 (中級) ---
        
        # --- レベル3 (上級) ---
        
    ]

    with app.app_context():
        print("データ投入を開始します...")
        
        count = 0
        for data in topics_data:
            # 重複チェック（同じレベル・同じトピック名ならスキップ）
            exists = LearningTopic.query.filter_by(
                level_id=data["level_id"], 
                topic=data["topic"]
            ).first()
            
            if exists:
                print(f"SKIP: {data['topic']} (既に存在します)")
                continue

            # 自動採番ロジック
            next_diff = get_next_difficulty(data["level_id"])
            
            # 登録
            new_topic = LearningTopic(
                level_id=data["level_id"],
                topic=data["topic"],
                difficulty=next_diff
            )
            db.session.add(new_topic)
            # 1件ずつコミットすることで、ループ内でもdifficultyが正しくインクリメントされるようにする
            db.session.commit() 
            
            print(f"ADDED: Level-{data['level_id']} No.{next_diff} : {data['topic']}")
            count += 1

        print(f"完了！ {count}件の単元を追加しました。")

if __name__ == "__main__":
    add_topics()