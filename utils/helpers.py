"""
Aether — Utility Helpers
------------------------------------------------
Small, dependency-free helper functions used across routes/services, plus
the mock practitioner dataset used to seed the database on first run.
"""

import re
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def is_valid_date(value: str) -> bool:
    """Expects YYYY-MM-DD."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def is_valid_time(value: str) -> bool:
    """Expects HH:MM (24hr). Empty string is allowed (unknown birth time)."""
    if not value:
        return True
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


def new_session_id() -> str:
    import uuid

    return uuid.uuid4().hex


def paginate(query, page: int, per_page: int):
    """Thin wrapper around Flask-SQLAlchemy's paginate for consistent API responses."""
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": result.items,
        "page": result.page,
        "pages": result.pages,
        "total": result.total,
        "has_next": result.has_next,
        "has_prev": result.has_prev,
    }


# ---------------------------------------------------------------------------
# Mock practitioner marketplace data — used only to seed SQLite on first run.
# ---------------------------------------------------------------------------
MOCK_EXPERTS = [
    {
        "name": "Maya Lindqvist",
        "photo_url": "/static/images/experts/maya-lindqvist.jpg",
        "experience_years": 12,
        "location": "Stockholm, Sweden (Online)",
        "languages": ["English", "Swedish"],
        "rating": 4.9,
        "review_count": 214,
        "specialization": ["Reiki", "Sound Healing"],
        "pricing": "$60 / session",
        "availability": "Mon–Fri, evenings (CET)",
        "bio": "Maya blends traditional Usui Reiki with therapeutic sound "
        "baths, helping clients release stored tension and reconnect "
        "with a sense of calm.",
    },
    {
        "name": "Aarav Mehta",
        "photo_url": "/static/images/experts/aarav-mehta.jpg",
        "experience_years": 9,
        "location": "Pune, India (Online & In-person)",
        "languages": ["English", "Hindi", "Marathi"],
        "rating": 4.8,
        "review_count": 178,
        "specialization": ["Breathwork", "Meditation"],
        "pricing": "$35 / session",
        "availability": "Tue–Sun, mornings (IST)",
        "bio": "Aarav trained under classical pranayama lineages and now "
        "guides breath-led sessions focused on nervous-system regulation.",
    },
    {
        "name": "Elena Rossi",
        "photo_url": "/static/images/experts/elena-rossi.jpg",
        "experience_years": 15,
        "location": "Florence, Italy (Online)",
        "languages": ["English", "Italian"],
        "rating": 5.0,
        "review_count": 301,
        "specialization": ["Aura Cleansing", "Reiki"],
        "pricing": "$75 / session",
        "availability": "Wed–Sat, afternoons (CET)",
        "bio": "Elena's practice centres on gentle energy clearing, "
        "helping clients feel lighter, grounded, and re-aligned.",
    },
    {
        "name": "Noah Bennett",
        "photo_url": "/static/images/experts/noah-bennett.jpg",
        "experience_years": 7,
        "location": "Austin, Texas, USA (Online)",
        "languages": ["English"],
        "rating": 4.7,
        "review_count": 96,
        "specialization": ["Past Life Regression", "Meditation"],
        "pricing": "$90 / session",
        "availability": "Weekends only (CST)",
        "bio": "Noah uses gentle guided regression techniques to help "
        "clients explore recurring life patterns in a safe container.",
    },
    {
        "name": "Priya Nair",
        "photo_url": "/static/images/experts/priya-nair.jpg",
        "experience_years": 11,
        "location": "Kochi, India (Online)",
        "languages": ["English", "Malayalam", "Tamil"],
        "rating": 4.9,
        "review_count": 245,
        "specialization": ["Sound Healing", "Breathwork"],
        "pricing": "$40 / session",
        "availability": "Mon–Sat, flexible (IST)",
        "bio": "Priya combines Himalayan singing bowls with breathwork to "
        "support deep rest and emotional release.",
    },
    {
        "name": "Liam O'Connor",
        "photo_url": "/static/images/experts/liam-oconnor.jpg",
        "experience_years": 6,
        "location": "Dublin, Ireland (Online)",
        "languages": ["English"],
        "rating": 4.6,
        "review_count": 58,
        "specialization": ["Meditation", "Aura Cleansing"],
        "pricing": "$30 / session",
        "availability": "Daily, evenings (GMT)",
        "bio": "Liam teaches accessible, science-informed meditation "
        "practices for people new to holistic wellness.",
    },
]
