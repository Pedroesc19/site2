import logging
import time
from collections import defaultdict
from flask import (
    Blueprint, render_template, request,
    flash, redirect, url_for, jsonify
)
from hackerservice.adapters.monero_rpc import create_xmr_subaddress
from hackerservice.adapters.bitcoin_hd import create_btc_address
from hackerservice.services.pricing import fetch_xmr_usd_rate, fetch_btc_usd_rate
from hackerservice.services.qr import generate_monero_qr, generate_qr_data_uri
from hackerservice.services.captcha import new_captcha, validate
from hackerservice.extensions import db
from hackerservice.models import Order, Affiliate

logger = logging.getLogger(__name__)
bp = Blueprint('services', __name__, template_folder='../templates')

# ──────────────────────────────────────────────
# Catalogue (unchanged)
# ──────────────────────────────────────────────
services = [
    # ── SOCIAL / PERSONAL ────────────────────
    {
        "category": "Social & Personal",
        "slug": "account_takeover",
        "name": "Premium Social-Account Hijack",
        "price": "$100 std / $400-500 VIP",
        "coins": "BTC • XMR",
        "pitch": "Full takeover of WhatsApp / Instagram in 24–72 h.",
        "price_usd": 15,
        "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "sim_swap",
        "name": "Zero-Day SIM-Swap Exploit",
        "price": "$5 000",
        "coins": "BTC",
        "pitch": "One-click carrier takeover script + docs.",
        "price_usd": 5000,
        "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "grade_change",
        "name": "GradeForge",
        "price": "$200 avg / job",
        "coins": "BTC • XMR",
        "pitch": "Stealth SIS/LMS grade & exam modification.",
        "price_usd": 200,
        "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "doxing",
        "name": "Reputation Destroy & Dox Pack",
        "price": "$500",
        "coins": "BTC • XMR",
        "pitch": "Deep-dive OSINT plus fake docs & legal spam.",
        "price_usd": 500,
        "type": "single",
    },

    # ── ATTACK TOOLS ─────────────────────────
    {
        "category": "Attack Tools",
        "slug": "ddos_booter",
        "name": "Instant DDoS Blaster",
        "price": "$50",
        "coins": "BTC • XMR",
        "pitch": "100 Gbps stresser jobs in minutes via API.",
        "price_usd": 50,
        "type": "single",
    },
    {
        "category": "Attack Tools",
        "slug": "raas_kit",
        "name": "WannaCry",
        "price": "$100",
        "coins": "BTC",
        "pitch": "Locker builder + portal;",
        "price_usd": 100,
        "type": "single",
    },
    {
        "category": "Attack Tools",
        "slug": "malware_phish_kit",
        "name": "PhishPro Malware Bundle",
        "price": "$100 mo",
        "coins": "BTC • XMR",
        "pitch": "Fresh malware & fake-shop templates; auto-download.",
        "price_usd": 100,
        "type": "single",
    },

    # ── DATA & CREDENTIALS ───────────────────
    {
        "category": "Data Leaks",
        "slug": "coinbase_db",
        "name": "Coinbase 250 K Customer Leak",
        "price": "$150",
        "coins": "BTC • XMR",
        "pitch": "Names, phones, e-mails — direct link on purchase.",
        "price_usd": 150,
        "type": "single",
    },
    {
        "category": "Data Leaks",
        "slug": "code_sign_cert",
        "name": "Enterprise Code-Sign Cert (EV)",
        "price": "$500",
        "coins": "BTC • XMR",
        "pitch": "EV/OV PFX + passphrase via shell corp.",
        "price_usd": 500,
        "type": "single",
    },
]

def grouped_services():
    buckets = defaultdict(list)
    for s in services:
        buckets[s["category"]].append(s)
    return buckets

def safe_get_rates(usd):
    try:
        xmr = usd / fetch_xmr_usd_rate()
    except Exception as e:
        logger.warning("XMR rate error: %s", e)
        xmr = usd / 150.0
    try:
        btc = usd / fetch_btc_usd_rate()
    except Exception as e:
        logger.warning("BTC rate error: %s", e)
        btc = usd / 65000.0
    return round(xmr, 12), round(btc, 8)

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@bp.route('/services')
def list_services():
    return render_template('services.html', grouped=grouped_services())

@bp.route('/service/<slug>', methods=['GET','POST'])
def service_detail(slug):
    svc = next((s for s in services if s['slug'] == slug), None)
    if not svc:
        flash('Service not found.', 'error')
        return redirect(url_for('services.list_services'))
    if request.method == 'POST':
        if not validate(request.form.get('captcha','')):
            flash('Captcha incorrect.', 'error')
        else:
            return redirect(url_for('services.service_payment',
                                     slug=slug, usd=svc['price_usd']))
    return render_template('service_detail.html',
                           service=svc,
                           captcha_img=new_captcha())

@bp.route('/service/<slug>/pay', methods=['GET', 'POST'])
def service_payment(slug):
    svc = next((s for s in services if s['slug'] == slug), None)
    if not svc:
        flash('Service not found.', 'error')
        return redirect(url_for('services.list_services'))

    usd_total = float(request.args.get('usd', svc['price_usd']))

    # Base crypto amounts for GET
    base_xmr_amt, base_btc_amt = safe_get_rates(usd_total)
    xmr_str = f"{base_xmr_amt:.12f}".rstrip('0').rstrip('.')
    btc_str = f"{base_btc_amt:.8f}"

    if request.method == 'POST':
        promo_code = request.form.get('promo_code', '').strip().upper() or None
        method     = request.form.get('method')

        affiliate    = None
        discount_usd = 0.0
        commission_usd = 0.0
        usd_due      = usd_total

        # 1) Apply discount
        if promo_code:
            affiliate = Affiliate.query.filter_by(code=promo_code, is_active=True).first()
            if not affiliate:
                flash('Invalid or inactive promo code.', 'error')
                return redirect(request.url)

            # Discount is % of original price
            discount_usd = round(
                usd_total * (float(affiliate.discount_pct) / 100), 2
            )
            usd_due = usd_total - discount_usd

            # Commission is % of the discounted price
            commission_usd = round(
                usd_due * (float(affiliate.commission_pct) / 100), 2
            )

            # Recalculate crypto amounts on net price
            xmr_amt, btc_amt = safe_get_rates(usd_due)
            xmr_str = f"{xmr_amt:.12f}".rstrip('0').rstrip('.')
            btc_str = f"{btc_amt:.8f}"
        else:
            # No code: no discount, no commission; use base amounts
            xmr_amt, btc_amt = base_xmr_amt, base_btc_amt

        # 2) Create & persist the Order
        order = Order(
            slug=slug,
            usd_amount=usd_total,
            discount_usd=discount_usd,
            commission_usd=commission_usd,
            affiliate_id=(affiliate.id if affiliate else None),
            status='pending'
        )

        try:
            # 3) Generate deposit address and set coin fields
            if method == 'xmr':
                addr = create_xmr_subaddress(slug)
                order.xmr_address = addr
                order.xmr_amount  = xmr_amt
            elif method == 'btc':
                addr = create_btc_address(slug)
                order.btc_address = addr
                order.btc_amount  = btc_amt
            else:
                flash('Select a payment method.', 'error')
                return redirect(request.url)

            db.session.add(order)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logger.exception('Error generating payment address:')
            flash(f'Failed to generate address: {e}', 'error')
            return redirect(request.url)

        # 4) Render invoice with full breakdown
        crypto = 'XMR' if method == 'xmr' else 'BTC'
        amount_crypto = xmr_str if method == 'xmr' else btc_str
        qr = (generate_monero_qr(addr, xmr_amt)
              if method == 'xmr'
              else generate_qr_data_uri(f"bitcoin:{addr}?amount={btc_str}"))

        return render_template('service_invoice.html',
                               service=svc,
                               usd=usd_due,
                               discount_usd=discount_usd,
                               commission_usd=commission_usd,
                               discount_code=promo_code,
                               amount_crypto=amount_crypto,
                               crypto=crypto,
                               address=addr,
                               qr=qr)

    # GET → standard payment options
    return render_template('service_payment.html',
                           service=svc,
                           usd=usd_total,
                           xmr_amt=xmr_str,
                           btc_amt=btc_str)

# ──────────────────────────────────────────────
# AJAX endpoint for live rate updates
# ──────────────────────────────────────────────
@bp.route('/rates')
def rates():
    """
    AJAX endpoint: given ?usd=<float>, returns JSON with
    recalculated xmr_amt and btc_amt based on live rates.
    """
    try:
        usd = float(request.args.get('usd', 0))
    except ValueError:
        return jsonify(error='invalid usd'), 400

    try:
        xmr_rate = fetch_xmr_usd_rate()
        btc_rate = fetch_btc_usd_rate()
        xmr_amt  = round(usd / xmr_rate, 12)
        btc_amt  = round(usd / btc_rate, 8)
        return jsonify(
            xmr_amt=f"{xmr_amt:.12f}",
            btc_amt=f"{btc_amt:.8f}",
            timestamp=int(time.time())
        )
    except Exception as e:
        logger.exception('Rate fetch error: %s', e)
        return jsonify(error=str(e)), 500

