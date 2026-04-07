###############################################################################################
# ███████╗███████╗ ██████╗██╗   ██╗██████╗ ██╗████████╗██╗   ██╗     ██████╗ ███████╗███████╗ #
# ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██║╚══██╔══╝╚██╗ ██╔╝     ██╔══██╗██╔════╝██╔════╝ #
# ███████╗█████╗  ██║     ██║   ██║██████╔╝██║   ██║    ╚████╔╝█████╗██████╔╝███████╗███████╗ #
# ╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██║   ██║     ╚██╔╝ ╚════╝██╔══██╗╚════██║╚════██║ #
# ███████║███████╗╚██████╗╚██████╔╝██║  ██║██║   ██║      ██║        ██║  ██║███████║███████║ #
# ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝        ╚═╝  ╚═╝╚══════╝╚══════╝ #
###############################################################################################

# Security RSS Feed

Ein Flask-basierter RSS-Aggregator für IT-Sicherheitsnachrichten. Sammelt Artikel aus deutschen und englischen Sicherheitsquellen, filtert nach konfigurierbaren Prioritätswörtern und stellt sie übersichtlich im Browser dar.

## Features

- **Automatischer Feed-Abruf** aus 8 Quellen (BSI, Heise, CERT-Bund, CISA, u.a.)
- **Priority Words Filter** – nur relevante Artikel werden angezeigt (z.B. Microsoft, NIS2, Dell)
- **Admin-UI** unter `/admin` – Priority Words zur Laufzeit hinzufügen/entfernen & Feeds manuell aktualisieren
- **Berichte** unter `/reports` – wichtige Artikel nach Datum gruppiert
- **Volltextsuche** über alle gecachten Artikel
- **Deduplizierung** – gleiche Artikel aus verschiedenen Quellen erscheinen nur einmal
- **Fehlerseiten** für 404, 500 und 503

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

## Voraussetzungen

- Python 3.7 oder höher
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
pip install -r requirements.txt
```

## Starten

```bash
python run.py
```

App im Browser öffnen: [http://127.0.0.1:5000](http://127.0.0.1:5000)

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

# NixOS
nix-env -iA nixpkgs.tmux

# Neue Session starten
tmux new -s security-rss

# App starten
python run.py

# Session im Hintergrund lassen: Strg+B, dann D
# Session wieder aufrufen
tmux attach -t security-rss
```

## Projektstruktur

```
rss-feed/
├── app/
│   ├── __init__.py          # App-Factory, Blueprints, Fehlerhandler
│   ├── config.py            # RSS-Feeds, Pfade
│   ├── database.py          # DB-Init, Priority Words CRUD
│   ├── feeds.py             # Feed-Abruf & Parsing
│   ├── models.py            # Artikel lesen/schreiben
│   ├── routes/
│   │   ├── main.py          # / (Startseite)
│   │   ├── search.py        # /search
│   │   ├── reports.py       # /reports
│   │   └── admin.py         # /admin
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
