print("--- !!! app.py が読み込まれました !!! ---") # <-- デバッグ用

import logging

from flask import Flask, request, render_template
from flask_cors import CORS

### メール関連
from flask_mail import Mail, Message
import os

from dotenv import load_dotenv

load_dotenv()
###


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

### ロギング
app.logger.setLevel(logging.DEBUG)

app.logger.critical("fatal error")
app.logger.error("error")
app.logger.warning("warning")
app.logger.info("info")
app.logger.debug("debug")
###

CORS(app)

class Dammy_user:
    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.name = name

### ダミーデータ返却（デバッグ用）
def return_dammy():
    user = Dammy_user("admin@example.com", "password", "admin")

###

@app.route("/", methods=["get","POST"])
def authentication_at_email_address():
    if request.method == "POST":
        email = request.form["email"]

        # メール送信テスト（デバッグ用）
        send_email(email,"test","test_mail",admin_name="名無しの専門学生")
        #

        return f"Hello, {email}!"
    else:
        return "Hello, Guest!"
    

### メール機能
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "True").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

app.config["MAIL_DEBUG"] = True

mail = Mail(app)

def send_email(to, subject, template, **kwargs):
    msg = Message(subject, recipients=[to])
    msg.body = render_template(template+".txt",**kwargs)
    msg.html = render_template(template+".html",**kwargs)
    # mail.send(msg)
    try:
        # app.logger.info(f"--- [Mail] Sending email to {to}...")
        print(f"--- [Mail] Sending email to {to}...")
        mail.send(msg)
        # app.logger.info(f"--- [Mail] Successfully sent email to {to}")
        print(f"--- [Mail] Successfully sent email to {to}")
    except Exception as e:
        # エラーが発生した場合、ターミナルにログを出力
        # app.logger.error(f"--- [Mail] FAILED to send email to {to} ---")
        # app.logger.error(f"--- [Mail] Error: {e}")
        print(f"--- [Mail] FAILED to send email to {to} ---")
        print(f"--- [Mail] Error: {e}")
###