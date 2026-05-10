from flask import Blueprint, render_template, request
from app.models import get_cached_articles
from app.feeds import prioritized_entries, score_article, tag_mitre
from app.database import get_priority_words

bp = Blueprint("reports", __name__)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@bp.route("/reports")
def reports():
    priority_words = get_priority_words()
    reports_data: dict[str, list] = {}

    for source, entries in get_cached_articles().items():
        for entry in entries:
            # important-Flag live neu berechnen
            entry["important"] = any(
                w.lower() in entry["title"].lower() for w in priority_words
            )
            if not entry["important"]:
                continue

            # Severity/MITRE für Altdaten ergänzen falls leer
            if not entry.get("severity"):
                entry["severity"], entry["severity_score"] = score_article(entry["title"])
            if not entry.get("mitre_tags"):
                entry["mitre_tags"] = tag_mitre(entry["title"])

            date = entry["published"].split(" ")[0]
            reports_data.setdefault(date, []).append(entry)

    # Innerhalb jedes Tages nach Severity sortieren
    for date in reports_data:
        reports_data[date].sort(
            key=lambda e: SEVERITY_ORDER.get(e.get("severity", "LOW"), 3)
        )

    return render_template(
        "reports.html",
        reports=dict(sorted(reports_data.items(), reverse=True)),
    )