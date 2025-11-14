from flask import render_template, current_app
from flask_mail import Message
from .extensions import mail  # さきほど作成した mail オブジェクトをインポート

# app.py から send_email 関数を丸ごとここに移動する
def send_email(to, subject, template, **kwargs):
    
    # print() ではなく、 current_app を使うことで、
    # 実行中のFlaskアプリのロガー（app.logger）を安全に取得できる
    app = current_app._get_current_object()

    msg = Message(subject, recipients=[to])
    msg.body = render_template(template+".txt",**kwargs)
    msg.html = render_template(template+".html",**kwargs)
    
    try:
        app.logger.info(f"--- [Mail] Sending email to {to}...")
        mail.send(msg)  # この mail オブジェクトは app.py で初期化される
        app.logger.info(f"--- [Mail] Successfully sent email to {to}")
        
    except Exception as e:
        app.logger.error(f"--- [Mail] FAILED to send email to {to} ---")
        app.logger.error(f"--- [Mail] Error: {e}")