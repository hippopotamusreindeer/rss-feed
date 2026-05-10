import re
import time
import logging
import requests
import feedparser
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from app.config import RSS_FEEDS
from app.models import cache_articles
from app.database import get_priority_words

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Quellen bei denen CVEs auf der verlinkten HTML-Seite stehen (nicht im Feed)
# ---------------------------------------------------------------------------
CVE_SCRAPE_SOURCES = {
    "BSI Cyber-Sicherheitswarnungen",
    "CERT-Bund Security Advisories",  # via interne JSON-API (2 Requests pro Advisory)
}

# CERT-Bund Advisory-Name aus URL extrahieren
# z.B. https://wid.cert-bund.de/portal/wid/securityadvisory?name=WID-SEC-2026-1437
CERT_BUND_NAME_RE = re.compile(r"[?&]name=(WID-SEC-[\w-]+)", re.IGNORECASE)
CERT_BUND_UUID_URL = "https://wid.cert-bund.de/content/public/securityAdvisory/kurzinfo-uuid-by-name/{name}"
CERT_BUND_DATA_URL = "https://wid.cert-bund.de/content/public/content/{uuid}"

# Maximale parallele Scraping-Threads pro Quelle
SCRAPE_MAX_WORKERS = 5

# ---------------------------------------------------------------------------
# MITRE ATT&CK Keyword-Mapping
# ---------------------------------------------------------------------------
ATTACK_KEYWORDS = {
    "T1566 – Phishing":                     ["phishing", "spear phishing", "spearphishing"],
    "T1190 – Exploit Public-Facing App":    ["exploit", "remote code execution", "rce", "sqli", "sql injection"],
    "T1486 – Data Encrypted for Impact":    ["ransomware", "encryption", "ransom", "erpressung"],
    "T1078 – Valid Accounts":               ["credential", "password spray", "brute force", "zugangsdaten"],
    "T1059 – Command & Scripting":          ["powershell", "bash", "cmd", "skript", "script"],
    "T1071 – App Layer Protocol":           ["c2", "command and control", "c&c", "botnet"],
    "T1110 – Brute Force":                  ["brute force", "credential stuffing", "password guessing"],
    "T1203 – Exploitation for Client Exec": ["drive-by", "watering hole", "browser exploit"],
    "T1496 – Resource Hijacking":           ["cryptomining", "cryptojacking", "miner"],
    "T1140 – Deobfuscate/Decode Files":     ["obfuscation", "obfuskierung", "encoded payload"],
}

# ---------------------------------------------------------------------------
# Severity Scoring
# ---------------------------------------------------------------------------
CRITICAL_KEYWORDS = [
    "zero-day", "0-day", "actively exploited", "critical", "rce",
    "remote code execution", "ransomware", "erpressung", "kritisch",
    "aktiv ausgenutzt",
]
HIGH_KEYWORDS = [
    "high severity", "patch tuesday", "authentication bypass",
    "privilege escalation", "denial of service",
]
MEDIUM_KEYWORDS = [
    "medium", "moderate", "information disclosure",
]

# CERT-Bund / BSI nutzen deutsches <category>-Feld – direkt mappen
CATEGORY_MAP = {
    "kritisch": ("CRITICAL", 9),
    "hoch":     ("HIGH", 7),
    "mittel":   ("MEDIUM", 5),
    "niedrig":  ("LOW", 3),
    "info":     ("LOW", 3),
}

# ---------------------------------------------------------------------------
# NVD CVE Enrichment (für /api/cve/<id> Route)
# ---------------------------------------------------------------------------
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _fetch_cve_data(cve_id: str) -> dict | None:
    """Einzelnen CVE von der NVD API abrufen. Wird nur vom API-Blueprint genutzt."""
    try:
        resp = requests.get(
            NVD_API_URL,
            params={"cveId": cve_id},
            timeout=10,
            headers={"User-Agent": "SecurityRSSFeed/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            return None

        cve_item     = vulnerabilities[0].get("cve", {})
        descriptions = cve_item.get("descriptions", [])
        description  = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            descriptions[0]["value"] if descriptions else "Keine Beschreibung verfügbar.",
        )

        metrics = cve_item.get("metrics", {})
        cvss_score = cvss_severity = cvss_version = None
        for version_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            metric_list = metrics.get(version_key, [])
            if metric_list:
                cvss_data     = metric_list[0].get("cvssData", {})
                cvss_score    = cvss_data.get("baseScore")
                cvss_severity = cvss_data.get("baseSeverity") or metric_list[0].get("baseSeverity")
                cvss_version  = cvss_data.get("version", version_key)
                break

        return {
            "id":            cve_id,
            "description":   description[:300] + ("…" if len(description) > 300 else ""),
            "cvss_score":    cvss_score,
            "cvss_severity": cvss_severity,
            "cvss_version":  cvss_version,
        }
    except Exception as e:
        logger.warning(f"CVE-Lookup fehlgeschlagen für {cve_id}: {e}")
        return None


# ---------------------------------------------------------------------------
# HTML-Stripper
# ---------------------------------------------------------------------------
class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str):
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    if not html:
        return ""
    try:
        s = _HTMLStripper()
        s.feed(html)
        return s.get_text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


# ---------------------------------------------------------------------------
# CVE-IDs aus Text extrahieren (dedupliziert, max 15)
# ---------------------------------------------------------------------------
def _extract_cve_ids(text: str, limit: int = 15) -> str:
    seen: dict[str, None] = {}
    for cve in re.findall(r"CVE-\d{4}-\d+", text, re.IGNORECASE):
        seen[cve.upper()] = None
    return ",".join(list(seen.keys())[:limit])


# ---------------------------------------------------------------------------
# Detailseite scrapen – läuft parallel via ThreadPoolExecutor
# ---------------------------------------------------------------------------
_SCRAPE_SESSION = requests.Session()
_SCRAPE_SESSION.headers.update({
    "User-Agent":      "SecurityRSSFeed/1.0 (CVE-Scraper)",
    "Accept-Language": "de-DE,de;q=0.9",
})

_scrape_cache: dict[str, str] = {}  # URL → cve_ids_str


def clear_scrape_cache():
    """Cache leeren – nötig nach Bugfix damit bereits gecachte kaputte URLs neu abgerufen werden."""
    _scrape_cache.clear()
    logger.info("Scrape-Cache geleert.")


def _scrape_cves_from_url(url: str) -> tuple[str, str]:
    """
    Gibt (url, cve_ids_str) zurück.
    Tuple-Format weil as_completed keinen direkten Rückgabe-Kontext hat.
    """
    if not url or url == "#":
        return url, ""
    if url in _scrape_cache:
        return url, _scrape_cache[url]
    try:
        resp = _SCRAPE_SESSION.get(url, timeout=12)
        resp.raise_for_status()
        result = _extract_cve_ids(resp.text)
        _scrape_cache[url] = result
        logger.debug(f"Scraped {url} → {result or '(keine CVEs)'}")
        return url, result
    except Exception as e:
        logger.warning(f"Scraping fehlgeschlagen für {url}: {e}")
        _scrape_cache[url] = ""
        return url, ""


def _certbund_cves_from_url(url: str) -> tuple[str, str]:
    """
    CVEs für CERT-Bund Advisory über die interne JSON-API holen.
    Ablauf: advisory-name aus URL → UUID → kurzinfo JSON → cveIdListe
    Gibt (url, cve_ids_str) zurück.
    """
    if url in _scrape_cache:
        return url, _scrape_cache[url]

    try:
        # Advisory-Name aus URL extrahieren (z.B. WID-SEC-2026-1437)
        match = CERT_BUND_NAME_RE.search(url)
        if not match:
            logger.debug(f"Kein WID-Name in URL: {url}")
            _scrape_cache[url] = ""
            return url, ""

        name = match.group(1)

        # Schritt 1: UUID holen
        uuid_resp = _SCRAPE_SESSION.get(
            CERT_BUND_UUID_URL.format(name=name), timeout=10
        )
        uuid_resp.raise_for_status()
        uuid = uuid_resp.text.strip().strip('"')
        if not uuid or len(uuid) != 36:
            logger.warning(f"Ungültige UUID für {name}: {uuid!r}")
            _scrape_cache[url] = ""
            return url, ""

        # Schritt 2: Advisory-JSON mit UUID abrufen
        data_resp = _SCRAPE_SESSION.get(
            CERT_BUND_DATA_URL.format(uuid=uuid), timeout=10
        )
        data_resp.raise_for_status()
        data = data_resp.json()

        # CVEs aus cveIdListe extrahieren
        cve_ids = []
        for child in data.get("children", []):
            if child.get("type") == "cveIdListe":
                for cve_entry in child.get("children", []):
                    cve_id = cve_entry.get("properties", {}).get("cveId", "")
                    if cve_id:
                        cve_ids.append(cve_id.upper())

        result = ",".join(cve_ids[:15])
        _scrape_cache[url] = result
        logger.debug(f"CERT-Bund {name} → {result or '(keine CVEs)'}")
        return url, result

    except Exception as e:
        logger.warning(f"CERT-Bund API fehlgeschlagen für {url}: {e}")
        _scrape_cache[url] = ""
        return url, ""


def _bulk_scrape(links: list[str], source: str = "") -> dict[str, str]:
    """
    Scrapt mehrere URLs parallel.
    Wählt automatisch BSI-HTML-Scraper oder CERT-Bund-API je nach Quelle.
    """
    is_certbund = source == "CERT-Bund Security Advisories"
    scrape_fn   = _certbund_cves_from_url if is_certbund else _scrape_cves_from_url
    results: dict[str, str] = {}
    todo = [url for url in links if url not in _scrape_cache]
    for url in links:
        if url in _scrape_cache:
            results[url] = _scrape_cache[url]

    if not todo:
        return results

    logger.info(f"{'CERT-Bund API' if is_certbund else 'HTML-Scraping'}: {len(todo)} Links parallel (max {SCRAPE_MAX_WORKERS} Threads)…")
    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_fn, url): url for url in todo}
        for future in as_completed(futures):
            url, cve_ids_str = future.result()
            results[url] = cve_ids_str

    return results


# ---------------------------------------------------------------------------
# MITRE ATT&CK Tagging
# ---------------------------------------------------------------------------
def tag_mitre(text: str) -> list[str]:
    text_lower = text.lower()
    return [
        technique
        for technique, keywords in ATTACK_KEYWORDS.items()
        if any(kw in text_lower for kw in keywords)
    ]


# ---------------------------------------------------------------------------
# Severity Scoring
# ---------------------------------------------------------------------------
def score_article(title: str, summary: str = "", category: str = "") -> tuple[str, int]:
    """
    Severity bestimmen – Priorität:
    1. Explizites <category>-Feld (CERT-Bund, BSI: 'kritisch', 'hoch', 'mittel')
    2. Keyword-Matching im Titel/Summary
    """
    # <category> direkt auswerten wenn vorhanden
    cat = category.strip().lower()
    if cat in CATEGORY_MAP:
        return CATEGORY_MAP[cat]

    # Fallback: Keywords im Text
    text = (title + " " + summary).lower()
    if any(kw in text for kw in CRITICAL_KEYWORDS):
        return "CRITICAL", 9
    elif any(kw in text for kw in HIGH_KEYWORDS):
        return "HIGH", 7
    elif any(kw in text for kw in MEDIUM_KEYWORDS):
        return "MEDIUM", 5
    return "LOW", 3


# ---------------------------------------------------------------------------
# Date Parsing
# ---------------------------------------------------------------------------
def parse_entry_date(entry) -> datetime | None:
    date_attrs = [
        ("published_parsed", lambda x: datetime(*x[:6])),
        ("updated_parsed",   lambda x: datetime(*x[:6])),
        ("published",        lambda x: datetime.strptime(x, "%a, %d %b %Y %H:%M:%S %Z")),
        ("updated",          lambda x: datetime.strptime(x, "%a, %d %b %Y %H:%M:%S %Z")),
    ]
    for attr, parser in date_attrs:
        if attr in entry:
            try:
                return parser(entry[attr])
            except Exception as e:
                logger.warning(f"Datum-Parse fehlgeschlagen ({attr}) für '{entry.get('title', '?')}': {e}")
    return None


# ---------------------------------------------------------------------------
# Feed-Abruf (Hauptfunktion)
# ---------------------------------------------------------------------------
def fetch_feeds():
    two_weeks_ago  = datetime.now() - timedelta(days=14)
    priority_words = get_priority_words()
    clear_scrape_cache()  # alte/fehlerhafte Cache-Einträge verwerfen

    for source, url in RSS_FEEDS.items():
        needs_scraping = source in CVE_SCRAPE_SOURCES
        try:
            feed    = feedparser.parse(url)
            entries = []

            # Schritt 1: Alle Einträge parsen, CVEs aus Feed-Text extrahieren
            needs_detail_scrape: list[str] = []  # Links die noch gescrapt werden müssen

            for entry in feed.entries:
                published_date = parse_entry_date(entry)
                if not published_date or published_date < two_weeks_ago:
                    continue

                title         = entry.get("title", "No Title").strip()
                summary       = entry.get("summary", "")
                link          = entry.get("link", "#").strip()
                category      = entry.get("category", "").strip()
                clean_summary = _strip_html(summary)
                full_text     = title + " " + clean_summary

                important      = any(w.lower() in title.lower() for w in priority_words)
                severity_label, severity_score = score_article(title, clean_summary, category)
                mitre_tags     = tag_mitre(full_text)
                cve_ids_str    = _extract_cve_ids(full_text)

                # Für BSI/CERT-Bund: Links ohne CVEs im Feed zum Scrapen vormerken
                if needs_scraping and not cve_ids_str and link not in _scrape_cache:
                    needs_detail_scrape.append(link)

                entries.append({
                    "title":          title,
                    "link":           link,
                    "published":      published_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "important":      important,
                    "severity":       severity_label,
                    "severity_score": severity_score,
                    "mitre_tags":     mitre_tags,
                    "cve_ids":        cve_ids_str,  # ggf. noch leer, wird unten ergänzt
                })

            # Schritt 2: Detailseiten parallel scrapen (nur BSI/CERT-Bund)
            if needs_scraping and needs_detail_scrape:
                scraped = _bulk_scrape(needs_detail_scrape, source=source)
                # CVE-IDs in die bereits gebauten Entry-Dicts eintragen
                for entry_dict in entries:
                    if not entry_dict["cve_ids"]:
                        entry_dict["cve_ids"] = scraped.get(entry_dict["link"], "")

            cache_articles(source, entries)
            logger.info(f"{source}: {len(entries)} Artikel gecacht"
                        + (f", {len(needs_detail_scrape)} Seiten gescrapt" if needs_scraping else ""))

        except Exception as e:
            logger.error(f"Fehler beim Abrufen von {source}: {e}")


# ---------------------------------------------------------------------------
# Sortier-Hilfsfunktion für Templates
# ---------------------------------------------------------------------------
SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def prioritized_entries(entries: list) -> list:
    return sorted(
        entries,
        key=lambda e: (
            0 if e.get("important") else 1,
            SEVERITY_ORDER.get(e.get("severity", "LOW"), 3),
            e.get("published", ""),
        ),
        reverse=False,
    )