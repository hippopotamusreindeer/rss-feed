from flask import Blueprint, render_template
from app.models import get_cached_articles
from app.feeds import prioritized_entries
from app.database import get_priority_words

bp = Blueprint('reports', __name__)

@bp.route('/reports')
def reports():
    priority_words = get_priority_words()
    reports_data = {}

    for source, entries in get_cached_articles().items():
        for entry in entries:
            # important-Flag live neu berechnen (nicht aus DB-Cache)
            is_important = any(w.lower() in entry['title'].lower() for w in priority_words)
            if is_important:
                entry['important'] = True
                date = entry['published'].split(' ')[0]
                reports_data.setdefault(date, []).append(entry)

    return render_template('reports.html', reports=dict(sorted(reports_data.items(), reverse=True)))