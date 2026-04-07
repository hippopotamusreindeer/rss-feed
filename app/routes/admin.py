from flask import Blueprint, render_template, request, redirect, url_for
from app.database import get_priority_words, add_priority_word, delete_priority_word
from app.feeds import fetch_feeds

bp = Blueprint('admin', __name__)

@bp.route('/admin', methods=['GET'])
def admin():
    words = get_priority_words()
    updated = request.args.get('updated') == '1'
    return render_template('admin.html', words=words, updated=updated)

@bp.route('/admin/update_feeds', methods=['POST'])
def update_feeds():
    fetch_feeds()
    return redirect(url_for('admin.admin', updated='1'))

@bp.route('/admin/add', methods=['POST'])
def add_word():
    word = request.form.get('word', '').strip()
    if word:
        add_priority_word(word)
    return redirect(url_for('admin.admin'))

@bp.route('/admin/delete', methods=['POST'])
def delete_word():
    word = request.form.get('word', '').strip()
    if word:
        delete_priority_word(word)
    return redirect(url_for('admin.admin'))