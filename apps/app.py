from flask import Flask, request
from flask_cors import CORS

### メール関連
from flask_mail import Mail
import os
###

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

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

        return f"Hello, {email}!"
    else:
        return "Hello, Guest!"
    

### メール機能
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
app.config["MAIL_PORT"] = os.environ.get("MAIL_PORT")
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

mail = Mail(app)
###