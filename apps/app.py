from flask import Flask, request
from flask_cors import CORS

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