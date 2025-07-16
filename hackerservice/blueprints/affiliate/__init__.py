from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from hackerservice.extensions import db
from hackerservice.models import Affiliate, Commission

bp = Blueprint(
    "affiliate_portal",
    __name__,
    url_prefix="/affiliate",
    template_folder="../templates"
)

@bp.route("/", methods=["GET", "POST"])
@login_required
def dashboard():
    # Only affiliates may view this page
    if current_user.role != "affiliate":
        flash("Not authorised to view affiliate dashboard.", "error")
        return redirect(url_for("services.list_services"))

    # Must have a linked affiliate record
    if not current_user.affiliate_id:
        flash("No affiliate account linked to your user.", "error")
        return redirect(url_for("services.list_services"))

    aff = Affiliate.query.get(current_user.affiliate_id)
    if aff is None:
        flash("Affiliate record not found.", "error")
        return redirect(url_for("services.list_services"))

    # Update payout addresses
    if request.method == "POST":
        aff.btc_address = request.form.get("btc_address") or None
        aff.xmr_address = request.form.get("xmr_address") or None
        db.session.commit()
        flash("Payout settings saved", "success")
        return redirect(url_for("affiliate_portal.dashboard"))

    # Metrics
    unpaid_q = Commission.query.filter_by(
        affiliate_id=aff.id, status="accrued"
    )
    paid_q = Commission.query.filter_by(
        affiliate_id=aff.id, status="paid"
    )

    stats = {
        "unpaid_total": unpaid_q.with_entities(db.func.sum(Commission.usd_amount)).scalar() or 0,
        "paid_total":   paid_q.with_entities(db.func.sum(Commission.usd_amount)).scalar() or 0,
        "tx_count":     paid_q.count(),
    }

    return render_template(
        "affiliate/dashboard.html",
        affiliate=aff,
        unpaid=unpaid_q.order_by(Commission.created_ts.desc()).all(),
        paid=paid_q.order_by(Commission.paid_ts.desc()).limit(10).all(),
        stats=stats
    )

