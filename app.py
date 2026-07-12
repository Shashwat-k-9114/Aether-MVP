"""
Aether — Application Entrypoint
------------------------------------------------
Run locally:

    python app.py

Run with the Flask CLI:

    export FLASK_APP=app.py
    flask run

Deployment (Render / gunicorn):

    gunicorn "app:create_app()"
"""

import os

from flask import Flask, jsonify

from config import get_config
from database import init_db
from routes import register_routes


def create_app(config_object=None):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object or get_config())

    init_db(app)
    register_routes(app)
    register_error_handlers(app)

    @app.route("/health")
    def health_check():
        return jsonify({"status": "ok", "service": "aether-backend"})

    return app


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(500)
    def server_error(err):
        return jsonify({"error": "Something went wrong on our end."}), 500


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", True)
    app.run(host="0.0.0.0", port=port, debug=debug)
