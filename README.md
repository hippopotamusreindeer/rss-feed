```
###############################################################################################
# ███████╗███████╗ ██████╗██╗   ██╗██████╗ ██╗████████╗██╗   ██╗     ██████╗ ███████╗███████╗ #
# ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝     ██╔══██╗██╔════╝██╔════╝ #
# ███████╗█████╗  ██║     ██║   ██║██████╔╝██║   ██║    ╚████╔╝█████╗██████╔╝███████╗███████╗ #
# ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██║   ██║     ╚██╔╝ ╚════╝██╔══██╗╚════██║╚════██║ #
# ███████║███████╗╚██████╗╚██████╔╝██║  ██║██║   ██║      ██║        ██║  ██║███████║███████║ #
# ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝        ╚═╝  ╚═╝╚══════╝╚══════╝ #
###############################################################################################
```

# Security RSS Feed

Ein Flask-basierter RSS-Aggregator für IT-Sicherheitsnachrichten. Sammelt Artikel aus deutschen und englischen Sicherheitsquellen, reichert sie automatisch mit Threat-Intelligence-Daten an und stellt sie übersichtlich im Browser dar.

## Features

- **Automatischer Feed-Abruf** aus 14 Quellen (BSI, Heise, CERT-Bund, CISA, Bleeping Computer, u.a.)
- **CVE Auto-Enrichment** – CVE-IDs werden automatisch erkannt und per Klick mit CVSS-Score & Beschreibung aus der NVD API angereichert
- **MITRE ATT&CK Tagging** – Artikel werden automatisch gegen ATT&CK-Techniken getaggt (T1566, T1190, T1486, …)
- **Severity Scoring** – automatisches Bewerten von Artikeln als CRITICAL / HIGH / MEDIUM / LOW
- **Priority Words Filter** – nur relevante Artikel werden angezeigt (z.B. Microsoft, NIS2, Dell)
- **Admin-UI** unter `/admin` – Priority Words zur Laufzeit hinzufügen/entfernen & Feeds manuell aktualisieren
- **Berichte** unter `/reports` – wichtige Artikel nach Datum gruppiert
- **Volltextsuche** über alle gecachten Artikel
- **Deduplizierung** – gleiche Artikel aus verschiedenen Quellen erscheinen nur einmal
- **Fehlerseiten** für 404, 500 und 503

## Threat Intelligence Enrichment

### CVE Auto-Enrichment
CVE-Identifier (z.B. `CVE-2024-1234`) werden automatisch im Titel und Summary jedes Artikels erkannt. Per Klick auf einen CVE-Badge wird die [NVD API](https://nvd.nist.gov/) abgefragt und CVSS-Score, Severity und Beschreibung direkt im Artikel angezeigt.

Für BSI und CERT-Bund, die CVEs nicht im RSS-Feed selbst liefern, werden die Detailseiten automatisch gescrapt:
- **BSI**: statisches HTML-Scraping
- **CERT-Bund**: interne JSON-API (`kurzinfo-uuid-by-name` → `content/{uuid}`)

### MITRE ATT&CK Tagging
Artikel werden automatisch gegen ATT&CK-Techniken getaggt:

| Technik | Keywords |
|---|---|
| T1566 – Phishing | phishing, spear phishing |
| T1190 – Exploit Public-Facing App | exploit, RCE, SQL injection |
| T1486 – Data Encrypted for Impact | ransomware, encryption |
| T1078 – Valid Accounts | credential, brute force |
| T1059 – Command & Scripting | powershell, bash, script |
| … | … |

### Severity Scoring
| Level | Kriterien |
|---|---|
| 🔴 CRITICAL | zero-day, aktiv ausgenutzt, RCE, ransomware |
| 🟠 HIGH | authentication bypass, privilege escalation |
| 🟡 MEDIUM | information disclosure |
| ⚪ LOW | alles andere |

Bei CERT-Bund und BSI wird das `<category>`-Feld (`kritisch`, `hoch`, `mittel`) direkt als Severity übernommen.

## Quellen

| Quelle | Sprache |
|---|---|
| Heise Security | Deutsch |
| Golem Security | Deutsch |
| BSI Cyber-Sicherheitswarnungen | Deutsch |
| CERT-Bund Security Advisories | Deutsch |
| Allianz für Cybersicherheit | Deutsch |
| CSO Online | Deutsch |
| Dark Reading | Englisch |
| CISA | Englisch |
| Bleeping Computer | Englisch |
| Krebs on Security | Englisch |
| The Hacker News | Englisch |
| Recorded Future Blog | Englisch |
| MITRE ATT&CK Blog | Englisch |
| US-CERT Alerts | Englisch |

## Voraussetzungen

- Python 3.10 oder höher
- pip

## Installation

1. Repository klonen und ins Verzeichnis wechseln:

```bash
git clone https://github.com/hippopotamusreindeer/rss-feed.git
cd rss-feed
```

2. Virtuelle Umgebung erstellen und aktivieren:

```bash
python3 -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate
```

3. Abhängigkeiten installieren:

```bash
pip install -r app/requirements.txt
```

## Starten

```bash
python run.py
```

App im Browser öffnen: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Die Feeds werden beim Start automatisch im Hintergrund geladen – die App ist sofort erreichbar.

## Nützliche Befehle

Feeds manuell aktualisieren (CLI):
```bash
flask update_feeds
```

`requirements.txt` nach neuen Paketen aktualisieren:
```bash
pip freeze > requirements.txt
```

Virtuelle Umgebung deaktivieren:
```bash
deactivate
```

## Headless-Betrieb mit tmux (optional)

Damit die App im Hintergrund läuft, ohne dass das Terminal offen bleiben muss:

```bash
# tmux installieren (Debian/Ubuntu)
sudo apt update && sudo apt install tmux
```
### NixOS
```bash
nix-env -iA nixpkgs.tmux
```
### Neue Session starten
```bash
tmux new -s security-rss
```
# App starten
```bash
python run.py
```
# Session im Hintergrund lassen: Strg+B, dann D
# Session wieder aufrufen
```bash
tmux attach -t security-rss
```

## Projektstruktur

```
rss-feed/
├── app/
│   ├── __init__.py          # App-Factory, Blueprints, Fehlerhandler
│   ├── config.py            # RSS-Feeds, Pfade
│   ├── database.py          # DB-Init, Priority Words CRUD, Migration
│   ├── feeds.py             # Feed-Abruf, CVE-Scraping, MITRE-Tagging, Severity
│   ├── models.py            # Artikel lesen/schreiben (Upsert)
│   ├── routes/
│   │   ├── main.py          # / (Startseite)
│   │   ├── search.py        # /search
│   │   ├── reports.py       # /reports
│   │   ├── admin.py         # /admin
│   │   └── api.py           # /api/cve/<id> (NVD Lookup)
│   ├── templates/
│   │   ├── index.html
│   │   ├── search.html
│   │   ├── reports.html
│   │   ├── admin.html
│   │   └── error.html
│   └── static/
│       └── style.css
├── instance/                # SQLite-DBs (nicht im Repo)
├── run.py
└── requirements.txt
```
