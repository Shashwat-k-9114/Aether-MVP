"""
Aether — Database Models
------------------------------------------------
All persistence entities for the MVP:

    User            core identity + onboarding info
    BirthDetail     birth data + generated (mock) Janampatri
    ChatMessage     one message in a chat session (user or AI)
    Recommendation  a scored healing-modality recommendation
    Expert          a practitioner (mock marketplace data)
    Booking         a user's session booked with an Expert
    JournalEntry    a free-form journal / mood entry

Everything is intentionally simple (SQLite + SQLAlchemy) so it can be
swapped for Postgres in production by only changing DATABASE_URL.
"""

import json
import uuid
from datetime import datetime

from database import db


def _uuid():
    return uuid.uuid4().hex


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class JSONEncodedText(db.TypeDecorator):
    """Stores Python lists/dicts as JSON text — SQLite has no native JSON type."""

    impl = db.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value else None


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    gender = db.Column(db.String(30), nullable=True)  # optional, per spec
    onboarding_complete = db.Column(db.Boolean, default=False)

    birth_detail = db.relationship(
        "BirthDetail", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    chat_messages = db.relationship(
        "ChatMessage", backref="user", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )
    recommendations = db.relationship(
        "Recommendation", backref="user", cascade="all, delete-orphan"
    )
    journal_entries = db.relationship(
        "JournalEntry", backref="user", cascade="all, delete-orphan"
    )
    bookings = db.relationship("Booking", backref="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "gender": self.gender,
            "onboarding_complete": self.onboarding_complete,
            "created_at": self.created_at.isoformat(),
        }


class BirthDetail(db.Model, TimestampMixin):
    __tablename__ = "birth_details"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey("users.id"), nullable=False, unique=True)

    date_of_birth = db.Column(db.String(20), nullable=False)   # YYYY-MM-DD
    time_of_birth = db.Column(db.String(10), nullable=True)    # HH:MM
    place_of_birth = db.Column(db.String(200), nullable=False)

    # --- Generated (mock) Janampatri data --------------------------------
    moon_sign = db.Column(db.String(40))
    sun_sign = db.Column(db.String(40))
    ascendant = db.Column(db.String(40))
    nakshatra = db.Column(db.String(60))
    dominant_planet = db.Column(db.String(40))
    planetary_positions = db.Column(JSONEncodedText)  # list[dict]
    doshas = db.Column(JSONEncodedText)                # dict
    elements = db.Column(JSONEncodedText)               # dict
    lucky_numbers = db.Column(JSONEncodedText)           # list[int]
    lucky_colors = db.Column(JSONEncodedText)            # list[str]
    strengths = db.Column(JSONEncodedText)                # list[str]
    challenges = db.Column(JSONEncodedText)                # list[str]

    def to_dict(self):
        return {
            "date_of_birth": self.date_of_birth,
            "time_of_birth": self.time_of_birth,
            "place_of_birth": self.place_of_birth,
            "moon_sign": self.moon_sign,
            "sun_sign": self.sun_sign,
            "ascendant": self.ascendant,
            "nakshatra": self.nakshatra,
            "dominant_planet": self.dominant_planet,
            "planetary_positions": self.planetary_positions,
            "doshas": self.doshas,
            "elements": self.elements,
            "lucky_numbers": self.lucky_numbers,
            "lucky_colors": self.lucky_colors,
            "strengths": self.strengths,
            "challenges": self.challenges,
        }


class ChatMessage(db.Model, TimestampMixin):
    __tablename__ = "chat_messages"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(32), nullable=False, index=True)
    role = db.Column(db.String(10), nullable=False)  # "user" | "ai"
    content = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
        }


class Recommendation(db.Model, TimestampMixin):
    __tablename__ = "recommendations"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey("users.id"), nullable=False)
    session_id = db.Column(db.String(32), nullable=True, index=True)

    modality_name = db.Column(db.String(80), nullable=False)
    stars = db.Column(db.Integer, nullable=False)              # 1-5
    confidence_score = db.Column(db.Float, nullable=False)      # 0-100
    why_it_fits = db.Column(db.Text, nullable=False)
    benefits = db.Column(JSONEncodedText, nullable=False)        # list[str]
    expected_experience = db.Column(db.Text, nullable=False)
    session_duration = db.Column(db.String(40), nullable=False)
    estimated_price = db.Column(db.String(40), nullable=False)
    what_to_expect = db.Column(db.Text, nullable=False)
    is_saved = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "modality_name": self.modality_name,
            "stars": self.stars,
            "confidence_score": self.confidence_score,
            "why_it_fits": self.why_it_fits,
            "benefits": self.benefits,
            "expected_experience": self.expected_experience,
            "session_duration": self.session_duration,
            "estimated_price": self.estimated_price,
            "what_to_expect": self.what_to_expect,
            "is_saved": self.is_saved,
        }


class Expert(db.Model, TimestampMixin):
    __tablename__ = "experts"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    name = db.Column(db.String(120), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    languages = db.Column(JSONEncodedText, nullable=False)   # list[str]
    rating = db.Column(db.Float, nullable=False)
    review_count = db.Column(db.Integer, default=0)
    specialization = db.Column(JSONEncodedText, nullable=False)  # list[str] (modalities)
    pricing = db.Column(db.String(40), nullable=False)
    availability = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "photo_url": self.photo_url,
            "experience_years": self.experience_years,
            "location": self.location,
            "languages": self.languages,
            "rating": self.rating,
            "review_count": self.review_count,
            "specialization": self.specialization,
            "pricing": self.pricing,
            "availability": self.availability,
            "bio": self.bio,
        }


class Booking(db.Model, TimestampMixin):
    __tablename__ = "bookings"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey("users.id"), nullable=False)
    expert_id = db.Column(db.String(32), db.ForeignKey("experts.id"), nullable=False)
    session_datetime = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(20), default="upcoming")  # upcoming|completed|cancelled

    expert = db.relationship("Expert")

    def to_dict(self):
        return {
            "id": self.id,
            "expert": self.expert.to_dict() if self.expert else None,
            "session_datetime": self.session_datetime,
            "status": self.status,
        }


class JournalEntry(db.Model, TimestampMixin):
    __tablename__ = "journal_entries"

    id = db.Column(db.String(32), primary_key=True, default=_uuid)
    user_id = db.Column(db.String(32), db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(30), nullable=True)  # e.g. "calm", "anxious", "hopeful"

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "mood": self.mood,
            "created_at": self.created_at.isoformat(),
        }
