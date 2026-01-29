from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def get_serializer():
    """Auth機能専用のシリアライザー取得"""
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_reset_token(email):
    serializer = get_serializer()
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    serializer = get_serializer()
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        # 有効期限切れ、または改ざんされている場合
        return None