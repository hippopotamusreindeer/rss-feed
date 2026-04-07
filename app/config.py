import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

RSS_FEEDS = {
    'CSO Online':                   'https://www.csoonline.com/feed/?languages=de',
    'Allianz für Cybersicherheit':  'https://www.allianz-fuer-cybersicherheit.de/SiteGlobals/Functions/RSSFeed/RSSNewsfeed/ACS_RSSNewsfeed.xml?nn=532576',
    'Golem Security':               'https://rss.golem.de/rss.php?ms=security&feed=RSS2.0',
    'Heise Security':               'https://www.heise.de/security/rss/news.rdf',
    'CERT-Bund Security Advisories':'https://wid.cert-bund.de/content/public/securityAdvisory/rss',
    'BSI Cyber-Sicherheitswarnungen':'https://www.bsi.bund.de/SiteGlobals/Functions/RSSFeed/RSSNewsfeed/RSSNewsfeed_CSW.xml',
    'Darkreading (Englisch)':       'https://www.darkreading.com/rss.xml',
    'CISA gov (Englisch)':          'https://www.cisa.gov/cybersecurity-advisories/all.xml'
}

# Default-Wörter – werden beim ersten Start in die DB geschrieben
DEFAULT_PRIORITY_WORDS = ["Dell", "Microsoft", "M365", "365", "NIS2"]

def get_db_path(source_name: str) -> str:
    safe_name = (
        source_name.lower()
        .replace(' ', '_').replace('/', '_')
        .replace('ü', 'ue').replace('ä', 'ae').replace('ö', 'oe')
    )
    return os.path.join(INSTANCE_DIR, f"{safe_name}.db")

MERGED_DB_PATH = os.path.join(INSTANCE_DIR, 'merged.db')
PRIORITY_WORDS_DB_PATH = os.path.join(INSTANCE_DIR, 'settings.db')