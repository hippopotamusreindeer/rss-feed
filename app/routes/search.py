from flask import Blueprint, render_template, request
from collections import defaultdict
from app.models import get_cached_articles

bp = Blueprint('search', __name__)

@bp.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = defaultdict(list)
    if query:
        for source, entries in get_cached_articles().items():
            for entry in entries:
                if query in entry['title'].lower():
                    results[source].append(entry)
    return render_template('search.html', query=query, results=results)