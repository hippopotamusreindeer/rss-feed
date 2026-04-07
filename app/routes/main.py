from flask import Blueprint, render_template, request
from app.models import get_cached_articles
from app.database import get_priority_words

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    show_all = request.args.get('filter') == 'all'
    priority_words = get_priority_words()
    feeds = get_cached_articles()

    # important-Flag live neu berechnen
    for entries in feeds.values():
        for entry in entries:
            entry['important'] = any(w.lower() in entry['title'].lower() for w in priority_words)

    if not show_all:
        feeds = {
            source: [e for e in entries if e['important']]
            for source, entries in feeds.items()
            if any(e['important'] for e in entries)
        }

    return render_template('index.html', feeds=feeds, only_important=not show_all)