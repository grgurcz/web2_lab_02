from flask import Flask, Response, abort, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.config.update(
    SECRET_KEY="random_secret_key"
)

login_manager = LoginManager()
login_manager.init_app(app)

csrf = CSRFProtect(app)
CSRF_PROTECTED = False

comments = ["Random comment number 1", "Random comment number 2", "<script>alert('GOTCHA')</script>"]
user_accounts = [
    {
        'id': 1,
        'username': 'user1',
        'password': 'user1',
        'account_balance': 2000
    },
    {
        'id': 2,
        'username': 'user2',
        'password': 'user2',
        'account_balance': 500
    },
    {
        'id': 3,
        'username': 'attacker',
        'password': 'attacker',
        'account_balance': 0
    }
]


class User(UserMixin):
    ...


def get_user(user_id: int):
    for user in user_accounts:
        if int(user["id"]) == int(user_id):
            return user
    return None


@login_manager.user_loader
def user_loader(id: int):
    user = get_user(id)
    if user:
        user_model = User()
        user_model.id = user["id"]
        return user_model
    return None


@app.errorhandler(401)
def unauthorized(error):
    return Response("Not authorized"), 401


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/xss_disabled')
def xss_disabled():
    return render_template('xss_disabled.html', comments=comments)


@app.route('/xss_enabled')
def xss_enabled():
    return render_template('xss_enabled.html', comments=comments)


@app.route("/toggle_csrf_protected")
def toggle_csrf():
    global CSRF_PROTECTED
    CSRF_PROTECTED = not CSRF_PROTECTED
    return redirect(url_for("csrf_homepage"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if CSRF_PROTECTED:
        csrf.protect()
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        for user in user_accounts:
            if user["username"] == username and user["password"] == password:
                user_model = User()
                user_model.id = user["id"]
                login_user(user_model)
                return redirect(url_for("csrf_homepage"))
        
        return abort(401)

    if current_user.is_authenticated:
        return redirect(url_for("csrf_homepage"))

    return render_template("login.html")


@app.route("/csrf_homepage", methods=["GET", "POST"])
@login_required
def csrf_homepage():
    if CSRF_PROTECTED:
        csrf.protect()

    user = get_user(current_user.id)

    if request.method == "POST":
        amount = int(request.form.get("amount"))
        account = int(request.form.get("account"))

        transfer_to = get_user(account)

        if amount <= user["account_balance"] and transfer_to:
            user["account_balance"] -= amount
            transfer_to["account_balance"] += amount

    return render_template(
        "csrf_homepage.html",
        balance=user["account_balance"],
        username=user["username"],
        all_users=user_accounts,
        protected=CSRF_PROTECTED
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == '__main__':
   app.run(host='0.0.0.0')