from flask import Blueprint, render_template, request
from app.models import get_cached_articles
from app.database import get_priority_words
from app.feeds import score_article, tag_mitre
import re

bp = Blueprint("main", __name__)

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


@bp.route("/")
def index():
    show_all       = request.args.get("filter") == "all"
    sort_by        = request.args.get("sort", "severity")   # "severity" | "date"
    priority_words = get_priority_words()
    feeds          = get_cached_articles()

    # important-Flag + Severity live neu berechnen (Priority Words könnten sich geändert haben)
    for entries in feeds.values():
        for entry in entries:
            entry["important"] = any(
                w.lower() in entry["title"].lower() for w in priority_words
            )
            # Falls Severity noch nicht gesetzt (Altdaten)
            if not entry.get("severity"):
                entry["severity"], entry["severity_score"] = score_article(entry["title"])

            # MITRE-Tags live ergänzen falls leer (Altdaten)
            if not entry.get("mitre_tags"):
                entry["mitre_tags"] = tag_mitre(entry["title"])

    if not show_all:
        feeds = {
            source: [e for e in entries if e["important"]]
            for source, entries in feeds.items()
            if any(e["important"] for e in entries)
        }

    return render_template(
        "index.html",
        feeds=feeds,
        only_important=not show_all,
        sort_by=sort_by,
    )