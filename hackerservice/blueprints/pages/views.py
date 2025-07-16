from flask import Blueprint, render_template, redirect, url_for

bp = Blueprint('pages', __name__)

@bp.get('/')
def home():
    return redirect(url_for('services.list_services'))

@bp.get('/about')
def about():
    return render_template('about.html')

@bp.get('/contact')
def contact():
    return render_template('contact.html')
