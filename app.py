from flask import Flask, request

app = Flask(__name__)

class Dammy_user:
    def __init__(self, email, password, name):
        self.email = email
        self.password = password
        self.name = name

### ダミーデータ返却
def return_dammy():
    user = Dammy_user("admin@example.com", "password", "admin")

###

@app.route("/", methods=["get","post"])
def authentication_at_email_address():
    if request.method == "post":
        email = request.form["email"]
        
        return email
    else:
        return "Hello, Guest!"