"""
Aether — Database Bootstrap
------------------------------------------------
Holds the single SQLAlchemy() instance shared across the app (avoids
circular imports between app.py / models.py / routes.py) plus helpers to
initialise and seed the database.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Bind SQLAlchemy to the Flask app and create tables if needed."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        _seed_experts_if_empty()


def _seed_experts_if_empty():
    """Populate the experts table with mock practitioners on first run."""
    from models import Expert

    if Expert.query.first() is not None:
        return

    from utils.helpers import MOCK_EXPERTS

    for data in MOCK_EXPERTS:
        db.session.add(Expert(**data))
    db.session.commit()
