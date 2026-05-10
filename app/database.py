import os
import sqlite3
import logging

from app.config import (
    get_db_path, MERGED_DB_PATH, RSS_FEEDS,
    INSTANCE_DIR, PRIORITY_WORDS_DB_PATH, DEFAULT_PRIORITY_WORDS,
)

logger = logging.getLogger(__name__)


def get_connection(db_path: str):
    return sqlite3.connect(db_path)


# ---------------------------------------------------------------------------
# DDL – neue Spalten: severity, severity_score, mitre_tags, cve_ids
# ---------------------------------------------------------------------------
CREATE_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS articles (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        source         TEXT,
        title          TEXT,
        link           TEXT UNIQUE,
        published      TEXT,
        important      INTEGER,
        severity       TEXT    DEFAULT "LOW",
        severity_score INTEGER DEFAULT 3,
        mitre_tags     TEXT    DEFAULT "",
        cve_ids        TEXT    DEFAULT ""
    )
'''

CREATE_PRIORITY_WORDS_SQL = '''
    CREATE TABLE IF NOT EXISTS priority_words (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE NOT NULL
    )
'''

# Migrationsspalten – werden bei bestehenden DBs ergänzt, falls noch nicht vorhanden
MIGRATION_COLUMNS = [
    ("severity",       "TEXT    DEFAULT 'LOW'"),
    ("severity_score", "INTEGER DEFAULT 3"),
    ("mitre_tags",     "TEXT    DEFAULT ''"),
    ("cve_ids",        "TEXT    DEFAULT ''"),
]


def _migrate_db(conn: sqlite3.Connection):
    """Fehlende Spalten in bestehende Tabellen einfügen (idempotent)."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(articles)")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_def in MIGRATION_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_def}")
            logger.info(f"Migration: Spalte '{col_name}' hinzugefügt.")
    conn.commit()


def init_db():
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # Artikel-DBs pro Quelle
    for source in RSS_FEEDS:
        conn = get_connection(get_db_path(source))
        conn.execute(CREATE_TABLE_SQL)
        _migrate_db(conn)
        conn.commit()
        conn.close()

    # Merged DB
    conn = get_connection(MERGED_DB_PATH)
    conn.execute(CREATE_TABLE_SQL)
    _migrate_db(conn)
    conn.commit()
    conn.close()

    # Priority-Words DB
    conn = get_connection(PRIORITY_WORDS_DB_PATH)
    conn.execute(CREATE_PRIORITY_WORDS_SQL)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM priority_words")
    if cursor.fetchone()[0] == 0:
        for word in DEFAULT_PRIORITY_WORDS:
            conn.execute("INSERT OR IGNORE INTO priority_words (word) VALUES (?)", (word,))
    conn.commit()
    conn.close()

    logger.info("Alle DBs initialisiert / migriert.")


# ---------------------------------------------------------------------------
# Priority Words CRUD
# ---------------------------------------------------------------------------
def get_priority_words() -> list[str]:
    conn = get_connection(PRIORITY_WORDS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT word FROM priority_words ORDER BY word")
    words = [row[0] for row in cursor.fetchall()]
    conn.close()
    return words


def add_priority_word(word: str) -> bool:
    try:
        conn = get_connection(PRIORITY_WORDS_DB_PATH)
        conn.execute("INSERT OR IGNORE INTO priority_words (word) VALUES (?)", (word.strip(),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Priority Word: {e}")
        return False


def delete_priority_word(word: str) -> bool:
    try:
        conn = get_connection(PRIORITY_WORDS_DB_PATH)
        conn.execute("DELETE FROM priority_words WHERE word = ?", (word,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Fehler beim Löschen von Priority Word: {e}")
        return False