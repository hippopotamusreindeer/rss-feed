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

### Setup Security-RSS-Feed


Diese Anleitung beschreibt, wie du eine Flask-App in einer virtuellen Umgebung einrichtest und die notwendigen Abhängigkeiten installierst.

### Voraussetzungen
Python 3.7 oder höher muss installiert sein.
pip (Python-Paketmanager) ist verfügbar.

### Erstellen einer virtuellen Umgebung:


- Öffne ein Terminal und navigiere in das Projektverzeichnis:

``` bash
cd ~/Security-RSS-Feed
```

1. Erstelle eine virtuelle Umgebung:

``` bash
python3 -m venv venv
```
Ein neues Verzeichnis venv wird erstellt, in dem alle Abhängigkeiten installiert werden.

2. Virtuelle Umgebung aktivieren

**Linux/MacOS:**

``` bash
source venv/bin/activate
```
**Windows (PowerShell):**

``` bash
.\venv\Scripts\Activate
```
- Sobald die virtuelle Umgebung aktiv ist, ändert sich der Terminal-Prompt zu:

``` plaintext

(venv) user@hostname:~/Security-RSS-Feed/$
```

3. Abhängigkeiten installieren
4. 
- Stelle sicher, dass die virtuelle Umgebung aktiv ist (siehe oben).

- Installiere die benötigten Pakete aus der requirements.txt:

``` bash
pip install -r requirements.txt
```
- Überprüfe die installierten Pakete:

``` bash
pip freeze
```
- Du solltest folgende Pakete sehen:

``` plaintext
Flask==2.2.3
Flask-Cors==3.0.10
feedparser==6.0.10
werkzeug==2.2.2
```
4. Projekt starten
5. 
- Stelle sicher, dass die virtuelle Umgebung aktiv ist.

- Starte die Flask-App:

``` bash
python app.py
```

- Öffne die App in deinem Browser:

``` plaintext
http://127.0.0.1:5000
```
5. Zusätzliche Befehle
-Virtuelle Umgebung deaktivieren

``` bash
deactivate
```
Abhängigkeiten aktualisieren

- Falls du neue Pakete installierst, kannst du die requirements.txt aktualisieren:

``` bash
pip freeze > requirements.txt
```

## Installation von tmux (optional) - erforderlich damit die Anwendung headless läuft

``` bash
sudo apt update
sudo apt install tmux
```
Starten einer tmux-Session:

- Starte eine neue tmux-Session mit dem Namen meine_session:

``` bash

tmux new -s meine_session
```
- Wechsle in dein Projektverzeichnis:

``` bash
cd ~/Security-RSS-Feed
```
- Führe die app.py aus:

``` bash
python3 app.py
```
