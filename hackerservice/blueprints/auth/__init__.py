from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app
)
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from hackerservice.models import User
from hackerservice.extensions import login  # your LoginManager
from hackerservice.services.mathcaptcha import new_captcha, validate

bp = Blueprint("auth", __name__, template_folder="../templates")


@bp.before_app_request
def enforce_timeout():
    # Only enforce on authenticated users
    if current_user.is_authenticated:
        now = datetime.utcnow().timestamp()
        last = session.get("last_activity", now)
        timeout = current_app.permanent_session_lifetime.total_seconds()
        if now - last > timeout:
            # Logout and clear session on timeout
            logout_user()
            session.clear()
            flash("You have been logged out due to inactivity.", "info")
            return redirect(url_for("auth.login_view"))
        # Update last-activity timestamp
        session["last_activity"] = now
    # no return means continue processing


@bp.after_app_request
def add_no_cache_headers(response):
    # Prevent browser caching of protected pages
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@bp.route("/login", methods=["GET", "POST"])
def login_view():
    # If already authenticated, redirect immediately
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.index"))
        else:
            return redirect(url_for("affiliate_portal.dashboard"))

    if request.method == "POST":
        if not validate(request.form.get("captcha", "")):
            flash("Captcha incorrect", "error")
        else:
            username = request.form["username"]
            pwd = request.form["password"]
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, pwd):
                login_user(user)
                session.permanent = True
                session["last_activity"] = datetime.utcnow().timestamp()
                flash("Logged in", "success")
                if user.role == "admin":
                    return redirect(url_for("admin.index"))
                else:
                    return redirect(url_for("affiliate_portal.dashboard"))

            flash("Bad credentials", "error")

    return render_template("login.html", captcha_question=new_captcha())


@bp.route("/logout")
def logout_view():
    logout_user()
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("auth.login_view"))


# User loader for Flask-Login
@login.user_loader
def load_user(user_id):
    from hackerservice.models import User
    return User.query.get(int(user_id))

