import sqlite3
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from app.config import get_db_path, MERGED_DB_PATH

logger = logging.getLogger(__name__)

def get_connection(db_path):
    return sqlite3.connect(db_path)

def cache_articles(source: str, entries: list):
    """Artikel in quell-spezifische DB schreiben."""
    conn = get_connection(get_db_path(source))
    cursor = conn.cursor()
    for entry in entries:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO articles (source, title, link, published, important)
                VALUES (?, ?, ?, ?, ?)
            ''', (source, entry['title'], entry['link'], entry['published'], entry['important']))
        except Exception as e:
            logger.warning(f"Fehler beim Cachen: {e}")
    conn.commit()
    conn.close()
    _merge_into_global(source, entries)

def _merge_into_global(source: str, entries: list):
    """
    Deduplizierung: Link ist UNIQUE in merged.db.
    Doppelte Artikel aus verschiedenen Quellen werden ignoriert.
    """
    conn = get_connection(MERGED_DB_PATH)
    cursor = conn.cursor()
    for entry in entries:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO articles (source, title, link, published, important)
                VALUES (?, ?, ?, ?, ?)
            ''', (source, entry['title'], entry['link'], entry['published'], entry['important']))
        except Exception as e:
            logger.warning(f"Merge-Fehler: {e}")
    conn.commit()
    conn.close()

def get_cached_articles(use_merged=True):
    """
    use_merged=True  → aus deduplizierter merged.db lesen (Standard)
    use_merged=False → aus allen Einzel-DBs lesen
    """
    db_path = MERGED_DB_PATH
    two_weeks_ago = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d %H:%M:%S')

    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT source, title, link, published, important
        FROM articles
        WHERE published >= ?
        ORDER BY published DESC
    ''', (two_weeks_ago,))
    rows = cursor.fetchall()
    conn.close()

    articles = defaultdict(list)
    for source, title, link, published, important in rows:
        articles[source].append({
            'title': title, 'link': link,
            'published': published, 'important': bool(important)
        })
    return articles