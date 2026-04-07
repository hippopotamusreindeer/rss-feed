import feedparser
import logging
from datetime import datetime, timedelta
from app.config import RSS_FEEDS
from app.models import cache_articles
from app.database import get_priority_words

logger = logging.getLogger(__name__)

def parse_entry_date(entry):
    date_attrs = [
        ('published_parsed', lambda x: datetime(*x[:6])),
        ('updated_parsed',   lambda x: datetime(*x[:6])),
        ('published',        lambda x: datetime.strptime(x, "%a, %d %b %Y %H:%M:%S %Z")),
        ('updated',          lambda x: datetime.strptime(x, "%a, %d %b %Y %H:%M:%S %Z"))
    ]
    for attr, parser in date_attrs:
        if attr in entry:
            try:
                return parser(entry[attr])
            except Exception as e:
                logger.warning(f"Failed to parse {attr} for '{entry.get('title', 'Unknown')}': {e}")
    return None

def fetch_feeds():
    two_weeks_ago = datetime.now() - timedelta(days=14)
    priority_words = get_priority_words()          # immer aktuell aus DB

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            entries = []
            for entry in feed.entries:
                published_date = parse_entry_date(entry)
                if published_date and published_date >= two_weeks_ago:
                    title = entry.get('title', 'No Title')
                    entries.append({
                        'title':     title,
                        'link':      entry.get('link', '#'),
                        'published': published_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'important': any(w.lower() in title.lower() for w in priority_words)
                    })
            cache_articles(source, entries)
        except Exception as e:
            logger.error(f"Error fetching {source}: {e}")

def prioritized_entries(entries):
    important = [e for e in entries if e['important']]
    others    = [e for e in entries if not e['important']]
    return important + others