import secrets
import string
from flask import flash, redirect, url_for, request, render_template
from flask_login import current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash
from wtforms import StringField, PasswordField
from flask_admin.form import rules

from hackerservice.extensions import db
from hackerservice.models import User, Affiliate, Order, Commission

# ── Custom admin index with metrics & top affiliates ─────────────────
class MyAdminIndex(AdminIndexView):
    @expose("/")
    def index(self):
        if not (current_user.is_authenticated and current_user.role == "admin"):
            return self.render("admin/not_authorized.html")

        total_sales = (
            db.session.query(db.func.sum(Order.usd_amount))
            .filter(Order.status == "paid")
            .scalar() or 0
        )
        unpaid_comm = (
            db.session.query(db.func.sum(Commission.usd_amount))
            .filter(Commission.status == "accrued")
            .scalar() or 0
        )
        top_affs = (
            db.session.query(
                Affiliate.display_name,
                db.func.sum(Commission.usd_amount).label("earned"),
            )
            .join(Commission)
            .filter(Commission.status == "paid")
            .group_by(Affiliate.id)
            .order_by(db.desc("earned"))
            .limit(5)
            .all()
        )

        return self.render(
            "admin/dashboard.html",
            total_sales=total_sales,
            unpaid_commissions=unpaid_comm,
            top_affiliates=top_affs,
        )

# ── Helper to generate random passwords ───────────────────────────────
def random_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

# ── Base class enforcing admin-only access ───────────────────────────
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == "admin"
    can_view_details = True

# ── Affiliate admin: CRUD + username/password fields + auto-create user ─
class AffiliateAdmin(SecureModelView):
    name                 = "Affiliates"
    form_columns         = (
        "display_name",
        "code",
        "discount_pct",
        "commission_pct",
        "is_active",
        "username",
        "password",
        "btc_address",
        "xmr_address",
    )
    column_list          = ("id", "display_name", "code", "dicount_pct", "commission_pct", "is_active")
    column_editable_list = ("commission_pct", "is_active")

    # extra login fields
    form_extra_fields = {
        "username": StringField("Username (leave blank = code.lower())"),
        "password": PasswordField("Password (leave blank = random)"),
    }

    # group fields in the create form
    form_create_rules = (
        rules.FieldSet(("display_name","code", "discount_pct","commission_pct","is_active"), "Affiliate"),
        rules.FieldSet(("username","password"), "Login credentials"),
        rules.FieldSet(("btc_address","xmr_address"), "Payout addresses"),
    )

    def on_model_change(self, form, model, is_created):
        if is_created:
            # ensure model.id is assigned before linking
            db.session.flush()

            username = (form.username.data or model.code.lower()).strip()
            raw_pwd  = form.password.data or random_password()
            user = User(
                username=username,
                password_hash=generate_password_hash(raw_pwd),
                role="affiliate",
                affiliate_id=model.id,
            )
            db.session.add(user)
            flash(f"Credentials → user: {username}  pass: {raw_pwd}", "success")

# ── User admin: read-only + password reset ───────────────────────────
class UserAdmin(SecureModelView):
    name         = "Users"
    column_list  = ("id", "username", "role", "affiliate_id")
    can_create   = False
    can_edit     = False
    can_delete   = False

    @expose("/reset/<int:user_id>")
    def reset(self, user_id):
        user = User.query.get_or_404(user_id)
        new_pwd = random_password()
        user.password_hash = generate_password_hash(new_pwd)
        db.session.commit()
        flash(f"Password reset: {user.username} → {new_pwd}", "info")
        return redirect(url_for(".index_view"))

# ── Order & Commission admin ─────────────────────────────────────────
class OrderAdmin(SecureModelView):
    name = "Orders"

class CommissionAdmin(SecureModelView):
    name = "Commissions"

# ── Initialization ───────────────────────────────────────────────────
def init_admin(app):
    admin = Admin(
        app,
        name="HackerService Admin",
        url="/admin",
        index_view=MyAdminIndex(),
        template_mode="bootstrap3",
    )

    admin.add_view(
        AffiliateAdmin(
            Affiliate, db.session,
            endpoint="affiliates",
            url="affiliates"
        )
    )
    admin.add_view(
        UserAdmin(
            User, db.session,
            endpoint="users",
            url="users"
        )
    )
    admin.add_view(
        OrderAdmin(
            Order, db.session,
            endpoint="orders",
            url="orders",
            category="Sales"
        )
    )
    admin.add_view(
        CommissionAdmin(
            Commission, db.session,
            endpoint="commissions",
            url="commissions",
            category="Sales"
        )
    )

