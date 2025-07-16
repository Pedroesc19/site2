from flask import (
    Blueprint, render_template, redirect,
    url_for, request, session, flash
)
from hackerservice.services.captcha import new_captcha, validate

bp = Blueprint('pages', __name__)


@bp.before_app_request
def require_site_captcha():
    """Force a CAPTCHA check for first-time visitors."""
    if request.endpoint in (
        'pages.captcha',
        'static',
        'auth.login_view',
    ):
        return
    if not session.get('site_verified'):
        return redirect(url_for('pages.captcha', next=request.url))

@bp.get('/')
def home():
    return redirect(url_for('services.list_services'))

@bp.get('/about')
def about():
    return render_template('about.html')

@bp.get('/contact')
def contact():
    return render_template('contact.html')


@bp.route('/captcha', methods=['GET', 'POST'])
def captcha():
    next_url = request.args.get('next') or request.form.get('next') or url_for('pages.home')
    if request.method == 'POST':
        if validate(request.form.get('captcha', '')):
            session['site_verified'] = True
            return redirect(next_url)
        flash('Captcha incorrect.', 'error')
    return render_template('captcha.html', captcha_img=new_captcha(), next=next_url)
