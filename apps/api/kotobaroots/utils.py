# utils.py など
from apps.api.kotobaroots.models import MyphraseEnglish, MyphraseChinese, MyphraseKorean, MyphraseFrench

MYPHRASE_MODEL_MAP = {
    "english": MyphraseEnglish,
    "chinese": MyphraseChinese,
    "korean": MyphraseKorean,
    "french": MyphraseFrench
}