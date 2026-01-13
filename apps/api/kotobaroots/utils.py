# apps/api/kotobaroots/utils.py
### メールトークン関連
from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# 1. 定義したマイフレーズモデルをすべてインポート
from apps.api.kotobaroots.models import (
    MyphraseEnglish,
    MyphraseChinese,
    MyphraseKorean,
    MyphraseFrench
)

### 学習機能
import os
import json
import random
###

# 2. 言語名（小文字）とモデルクラスを紐付ける辞書を作成
# キーは Languageテーブルの language カラムの値（の小文字版）と一致させます
MYPHRASE_MODEL_MAP = {
    "english": MyphraseEnglish,
    "chinese": MyphraseChinese,
    "korean": MyphraseKorean,
    "french": MyphraseFrench,
}

def get_myphrase_model(language_name):
    """
    言語名を受け取り、対応するSQLAlchemyモデルクラスを返す関数
    """
    if not language_name:
        return None
    
    # 大文字・小文字の表記ゆれを防ぐため、小文字に統一してキー検索する
    normalized_name = language_name.lower()
    
    return MYPHRASE_MODEL_MAP.get(normalized_name)

def get_serializer():
    """Kotobaroots機能専用のシリアライザー取得"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_email_change_token(user_id, new_email):
    """
    メールアドレス変更用のトークンを生成
    payloadとして user_id と new_email を埋め込む
    """
    serializer = get_serializer()
    # saltを変えることで、パスワードリセット用のトークンと混同されないようにする
    return serializer.dumps(
        {"user_id": user_id, "new_email": new_email},
        salt="email-change-salt"
    )

def verify_email_change_token(token, expiration=3600):
    serializer = get_serializer()
    try:
        payload = serializer.loads(token, salt='email-change-salt', max_age=expiration)
        return payload
    except (SignatureExpired, BadSignature):
        # 有効期限切れ、または改ざんされている場合
        return None
    

### 学習機能
# 問題プリセット取得
def load_preset_questions(language, country, level, topic_filename, limit=10):
    """
    指定されたJSONから問題を読み込み、ランダムに抽出して返す
    
    Args:
        language (str): 言語フォルダ名 (例: 'english')
        country (str): 国フォルダ名 (例: 'america')
        level (str): レベルフォルダ名 (例: 'beginner')
        topic_filename (str): ファイル名 (例: 'subjunctive_mood')
        limit (int): 出題数 (デフォルト10)
    
    Returns:
        list: ランダムに抽出された問題リスト (失敗時は None)
    """
    try:
        # ファイル名に拡張子がない場合は付与
        if not topic_filename.endswith('.json'):
            topic_filename = f"{topic_filename}.json"

        # パスの構築: .../questions/{language}/{country}/{level}/{filename}
        # 例: apps/api/kotobaroots/questions/english/america/beginner/subjunctive_mood.json
        base_path = os.path.join(current_app.root_path, 'api', 'kotobaroots', 'questions')
        file_path = os.path.join(base_path, language, country, level, topic_filename)

        # デバッグ用ログ
        current_app.logger.debug(f"Loading questions from: {file_path}")

        if not os.path.exists(file_path):
            current_app.logger.warning(f"File not found: {file_path}")
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # JSON構造の正規化
        # 提供されたフォーマット通り { "questions": [...] } の形を想定
        questions_list = []
        if isinstance(data, dict) and "questions" in data:
            questions_list = data["questions"]
        elif isinstance(data, list):
            questions_list = data
        else:
            current_app.logger.warning(f"Invalid JSON format in {topic_filename}")
            return []

        # 問題数が足りない場合のハンドリング
        sample_size = min(len(questions_list), limit)
        
        # 重複なしランダム抽出
        selected_questions = random.sample(questions_list, sample_size)
        
        return selected_questions

    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON Decode Error in {file_path}: {e}")
        return None
    except Exception as e:
        current_app.logger.error(f"Error loading questions: {e}")
        return None
###