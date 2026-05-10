"""
app/routes/api.py
Stellt einen JSON-Endpunkt bereit, den das Frontend für CVE-Lookups nutzt.
GET /api/cve/<cve_id>  →  JSON mit CVSS-Score + Beschreibung
"""
from flask import Blueprint, jsonify
from app.feeds import _fetch_cve_data

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/cve/<cve_id>")
def cve_detail(cve_id: str):
    """NVD-Daten für eine CVE-ID abrufen und als JSON zurückgeben."""
    # Einfache Validierung
    import re
    if not re.fullmatch(r"CVE-\d{4}-\d+", cve_id, re.IGNORECASE):
        return jsonify({"error": "Ungültige CVE-ID"}), 400

    data = _fetch_cve_data(cve_id.upper())
    if data is None:
        return jsonify({"error": f"Keine NVD-Daten für {cve_id} gefunden."}), 404

    return jsonify(data)