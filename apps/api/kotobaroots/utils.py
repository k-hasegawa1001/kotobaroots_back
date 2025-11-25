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