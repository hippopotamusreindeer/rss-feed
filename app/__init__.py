import threading
from flask import Flask, render_template
from flask_cors import CORS
from app.database import init_db
from app.feeds import fetch_feeds, prioritized_entries


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.secret_key = "change-me-in-production"
    CORS(app)

    # Blueprints
    from app.routes.main    import bp as main_bp
    from app.routes.search  import bp as search_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.admin   import bp as admin_bp
    from app.routes.api     import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.context_processor
    def inject_helpers():
        return dict(prioritized_entries=prioritized_entries)

    # Fehlerseiten
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404,
                               title="Seite nicht gefunden",
                               message="Die angeforderte Seite existiert nicht."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500,
                               title="Serverfehler",
                               message="Ein interner Fehler ist aufgetreten."), 500

    @app.errorhandler(503)
    def service_unavailable(e):
        return render_template("error.html", code=503,
                               title="Dienst nicht verfügbar",
                               message="Der Dienst ist vorübergehend nicht erreichbar."), 503

    # CLI
    @app.cli.command("update_feeds")
    def update_feeds_cmd():
        fetch_feeds()
        print("Feeds updated.")

    # DB zuerst synchron initialisieren
    init_db()

    # Feed-Abruf im Hintergrund – blockiert den Start nicht
    t = threading.Thread(target=fetch_feeds, daemon=True, name="feed-fetcher")
    t.start()

    return app