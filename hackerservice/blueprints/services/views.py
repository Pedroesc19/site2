import logging
import time
from collections import defaultdict
from flask import (
    Blueprint, render_template, request,
    flash, redirect, url_for, jsonify
)
from hackerservice.adapters.monero_rpc import create_xmr_subaddress
from hackerservice.adapters.bitcoin_rpc import create_btc_address
from hackerservice.services.pricing import fetch_xmr_usd_rate, fetch_btc_usd_rate
from hackerservice.services.qr import generate_monero_qr, generate_qr_data_uri
from hackerservice.services.captcha import new_captcha, validate

logger = logging.getLogger(__name__)
bp = Blueprint('services', __name__, template_folder='../templates')

# ──────────────────────────────────────────────
# Catalogue
# ──────────────────────────────────────────────
services = [
    # ── SOCIAL / PERSONAL  ────────────────────
    {
        "category": "Social & Personal",
        "slug": "account_takeover",
        "name": "Premium Social-Account Hijack",
        "price": "$100 std / $400-500 VIP",
        "coins": "BTC • XMR",
        "pitch": "Full takeover of WhatsApp / Instagram in 24–72 h.",
        "price_usd": 100, "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "sim_swap",
        "name": "Zero-Day SIM-Swap Exploit",
        "price": "$5k",
        "coins": "BTC",
        "pitch": "One-click carrier takeover script + docs.",
        "price_usd": 5000, "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "grade_change",
        "name": "GradeForge",
        "price": "$200 avg / job",
        "coins": "BTC • XMR",
        "pitch": "Stealth SIS/LMS grade & exam modification.",
        "price_usd": 200, "type": "single",
    },
    {
        "category": "Social & Personal",
        "slug": "doxing",
        "name": "Reputation Destroy & Dox Pack",
        "price": "$500",
        "coins": "BTC • XMR",
        "pitch": "Deep-dive OSINT plus fake docs & legal spam.",
        "price_usd": 500, "type": "single",
    },

    # ── ATTACK TOOLS  ─────────────────────────
    {
        "category": "Attack Tools",
        "slug": "ddos_booter",
        "name": "Instant DDoS Blaster",
        "price": "$50",
        "coins": "BTC • XMR",
        "pitch": "100 Gbps stresser jobs in minutes via API.",
        "price_usd": 50, "type": "single",
    },
    {
        "category": "Attack Tools",
        "slug": "raas_kit",
        "name": "WannaCry",
        "price": "$100",
        "coins": "BTC",
        "pitch": "Locker builder + portal;",
        "price_usd": 100, "type": "single",
    },
    {
        "category": "Attack Tools",
        "slug": "malware_phish_kit",
        "name": "PhishPro Malware Bundle",
        "price": "$100 mo",
        "coins": "BTC • XMR",
        "pitch": "Fresh malware & fake-shop templates; auto-download.",
        "price_usd": 100, "type": "single",
    },

    # ── DATA & CREDENTIALS  ───────────────────
    {
        "category": "Data Leaks",
        "slug": "coinbase_db",
        "name": "Coinbase 250 K Customer Leak",
        "price": "$150",
        "coins": "BTC • XMR",
        "pitch": "Names, phones, e-mails — direct link on purchase.",
        "price_usd": 150, "type": "single",
    },
    {
        "category": "Data Leaks",
        "slug": "code_sign_cert",
        "name": "Enterprise Code-Sign Cert (EV)",
        "price": "$500",
        "coins": "BTC • XMR",
        "pitch": "EV/OV PFX + passphrase via shell corp.",
        "price_usd": 500, "type": "single",
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
    svc = next((s for s in services if s['slug']==slug), None)
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

@bp.route('/service/<slug>/pay', methods=['GET','POST'])
def service_payment(slug):
    svc = next((s for s in services if s['slug']==slug), None)
    if not svc:
        flash('Service not found.', 'error')
        return redirect(url_for('services.list_services'))
    usd = float(request.args.get('usd', svc['price_usd']))
    xmr_amt, btc_amt = safe_get_rates(usd)
    xmr_str = f"{xmr_amt:.12f}".rstrip('0').rstrip('.')
    btc_str = f"{btc_amt:.8f}"
    if request.method == 'POST':
        method = request.form.get('method')
        try:
            if method == 'xmr':
                addr = create_xmr_subaddress(slug)
                qr   = generate_monero_qr(addr, xmr_amt)
                return render_template('service_invoice.html',
                                       service=svc, usd=usd,
                                       amount_crypto=xmr_str,
                                       crypto='XMR',
                                       address=addr, qr=qr)
            elif method == 'btc':
                addr = create_btc_address(slug)
                uri  = f"bitcoin:{addr}?amount={btc_str}"
                qr   = generate_qr_data_uri(uri)
                return render_template('service_invoice.html',
                                       service=svc, usd=usd,
                                       amount_crypto=btc_str,
                                       crypto='BTC',
                                       address=addr, qr=qr)
            else:
                flash('Select a payment method.', 'error')
        except Exception as e:
            logger.exception('Payment address error: %s', e)
            flash(f'Cannot generate address: {e}', 'error')
    return render_template('service_payment.html',
                           service=svc, usd=usd,
                           xmr_amt=xmr_str, btc_amt=btc_str)

@bp.route('/rates')
def rates():
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

