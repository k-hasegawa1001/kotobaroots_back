# apps/api/kotobaroots/utils.py

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