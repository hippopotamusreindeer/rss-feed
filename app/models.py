import sqlite3
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from app.config import get_db_path, MERGED_DB_PATH

logger = logging.getLogger(__name__)


def get_connection(db_path):
    return sqlite3.connect(db_path)


# ---------------------------------------------------------------------------
# Upsert SQL – aktualisiert cve_ids/mitre_tags bei bereits bekannten Links
# ---------------------------------------------------------------------------
_UPSERT_SQL = """
    INSERT INTO articles
        (source, title, link, published, important,
         severity, severity_score, mitre_tags, cve_ids)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(link) DO UPDATE SET
        severity       = excluded.severity,
        severity_score = excluded.severity_score,
        mitre_tags     = excluded.mitre_tags,
        cve_ids        = excluded.cve_ids,
        important      = excluded.important
"""


def _entry_params(source: str, entry: dict) -> tuple:
    return (
        source,
        entry["title"],
        entry["link"],
        entry["published"],
        entry["important"],
        entry.get("severity", "LOW"),
        entry.get("severity_score", 3),
        ",".join(entry.get("mitre_tags", [])),
        entry.get("cve_ids", ""),
    )


def cache_articles(source: str, entries: list):
    """Artikel in quell-spezifische DB schreiben (upsert)."""
    conn = get_connection(get_db_path(source))
    cursor = conn.cursor()
    for entry in entries:
        try:
            cursor.execute(_UPSERT_SQL, _entry_params(source, entry))
        except Exception as e:
            logger.warning(f"Fehler beim Cachen: {e}")
    conn.commit()
    conn.close()
    _merge_into_global(source, entries)


def _merge_into_global(source: str, entries: list):
    """Deduplizierung: Link ist UNIQUE in merged.db (upsert)."""
    conn = get_connection(MERGED_DB_PATH)
    cursor = conn.cursor()
    for entry in entries:
        try:
            cursor.execute(_UPSERT_SQL, _entry_params(source, entry))
        except Exception as e:
            logger.warning(f"Merge-Fehler: {e}")
    conn.commit()
    conn.close()


def get_cached_articles(use_merged=True) -> defaultdict:
    """Liest Artikel aus merged.db, gibt geparste Listen zurück."""
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection(MERGED_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT source, title, link, published, important,
               severity, severity_score, mitre_tags, cve_ids
        FROM articles
        WHERE published >= ?
        ORDER BY published DESC
        """,
        (two_weeks_ago,),
    )
    rows = cursor.fetchall()
    conn.close()

    articles = defaultdict(list)
    for source, title, link, published, important, severity, severity_score, mitre_tags, cve_ids in rows:
        articles[source].append(
            {
                "title":          title,
                "link":           link,
                "published":      published,
                "important":      bool(important),
                "severity":       severity or "LOW",
                "severity_score": severity_score or 3,
                "mitre_tags":     [t for t in (mitre_tags or "").split(",") if t],
                "cve_ids":        [c for c in (cve_ids or "").split(",") if c],
            }
        )
    return articles