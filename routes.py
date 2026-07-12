"""
Aether — Routes
------------------------------------------------
All Flask routes for the MVP, grouped into blueprints:

    main_bp             page rendering (landing, onboarding, chat, dashboard)
    users_api           user creation + birth details + Janampatri
    chat_api            guided AI conversation
    recommendations_api healing recommendation engine
    experts_api         practitioner marketplace + bookings
    journal_api          journal / mood entries

Every /api/* route returns JSON. Page routes render Jinja templates (the
templates themselves are the next build phase — this file is backend-first
per the current request, so template rendering calls will 404 until those
files exist, but the API is fully functional and testable on its own,
e.g. with curl or Postman).
"""

from flask import Blueprint, jsonify, render_template, request, session

from database import db
from models import BirthDetail, Booking, ChatMessage, Expert, JournalEntry, Recommendation, User
from services.ai import get_ai_provider
from services.janampatri import generate_janampatri
from services.recommendations import generate_recommendations
from utils.helpers import is_valid_date, is_valid_email, is_valid_time, new_session_id

# ---------------------------------------------------------------------------
# Blueprints
# ---------------------------------------------------------------------------
main_bp = Blueprint("main", __name__)
users_api = Blueprint("users_api", __name__, url_prefix="/api/users")
chat_api = Blueprint("chat_api", __name__, url_prefix="/api/chat")
recommendations_api = Blueprint("recommendations_api", __name__, url_prefix="/api/recommendations")
experts_api = Blueprint("experts_api", __name__, url_prefix="/api/experts")
journal_api = Blueprint("journal_api", __name__, url_prefix="/api/journal")


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(users_api)
    app.register_blueprint(chat_api)
    app.register_blueprint(recommendations_api)
    app.register_blueprint(experts_api)
    app.register_blueprint(journal_api)


def error(message, status=400):
    return jsonify({"error": message}), status


def get_user_or_404(user_id):
    user = User.query.get(user_id)
    return user


# ===========================================================================
# PAGE ROUTES  (templates land in the next build phase)
# ===========================================================================

@main_bp.route("/")
def landing():
    return render_template("index.html")


@main_bp.route("/onboarding")
def onboarding_page():
    return render_template("onboarding.html")


@main_bp.route("/janampatri")
def janampatri_page():
    return render_template("janampatri.html")


@main_bp.route("/chat")
def chat_page():
    return render_template("chat.html")


@main_bp.route("/recommendations")
def recommendations_page():
    return render_template("recommendations.html")


@main_bp.route("/experts")
def experts_page():
    return render_template("experts.html")


@main_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


# ===========================================================================
# USERS + BIRTH DETAILS + JANAMPATRI
# ===========================================================================

@users_api.route("", methods=["POST"])
def create_user():
    """Step 1 of onboarding: name, email, optional gender."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    gender = (data.get("gender") or "").strip() or None

    if not name:
        return error("Name is required.")
    if not is_valid_email(email):
        return error("A valid email is required.")

    existing = User.query.filter_by(email=email).first()
    if existing:
        session["user_id"] = existing.id
        return jsonify(existing.to_dict()), 200

    user = User(name=name, email=email, gender=gender)
    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.id
    return jsonify(user.to_dict()), 201


@users_api.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)
    return jsonify(user.to_dict())


@users_api.route("/<user_id>/birth-details", methods=["POST"])
def submit_birth_details(user_id):
    """Step 2 of onboarding: DOB, time, place -> generates the Janampatri."""
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)

    data = request.get_json(silent=True) or {}
    dob = (data.get("date_of_birth") or "").strip()
    tob = (data.get("time_of_birth") or "").strip()
    place = (data.get("place_of_birth") or "").strip()

    if not is_valid_date(dob):
        return error("date_of_birth must be in YYYY-MM-DD format.")
    if not is_valid_time(tob):
        return error("time_of_birth must be in HH:MM format.")
    if not place:
        return error("place_of_birth is required.")

    chart = generate_janampatri(dob, tob, place)

    birth_detail = user.birth_detail or BirthDetail(user_id=user.id)
    birth_detail.date_of_birth = dob
    birth_detail.time_of_birth = tob or None
    birth_detail.place_of_birth = place
    for key, value in chart.items():
        setattr(birth_detail, key, value)

    user.onboarding_complete = True

    db.session.add(birth_detail)
    db.session.commit()

    return jsonify(birth_detail.to_dict()), 201


@users_api.route("/<user_id>/janampatri", methods=["GET"])
def get_janampatri(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)
    if not user.birth_detail:
        return error("Janampatri has not been generated yet.", 404)
    return jsonify(user.birth_detail.to_dict())


@users_api.route("/<user_id>/dashboard", methods=["GET"])
def dashboard_summary(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)

    saved_recs = [r.to_dict() for r in user.recommendations if r.is_saved]
    upcoming = [b.to_dict() for b in user.bookings if b.status == "upcoming"]
    recent_journal = [j.to_dict() for j in user.journal_entries[-5:]]
    sessions = sorted({m.session_id for m in user.chat_messages})

    return jsonify(
        {
            "user": user.to_dict(),
            "has_janampatri": user.birth_detail is not None,
            "saved_recommendations": saved_recs,
            "upcoming_bookings": upcoming,
            "recent_journal_entries": recent_journal,
            "chat_session_count": len(sessions),
            "total_recommendations": len(user.recommendations),
        }
    )


# ===========================================================================
# AI CHAT
# ===========================================================================

@chat_api.route("/start", methods=["POST"])
def start_chat():
    """Begins a new guided conversation session and returns the opener."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    user = get_user_or_404(user_id)
    if not user:
        return error("Valid user_id is required.", 404)

    session_id = new_session_id()
    provider = get_ai_provider(_current_provider_name())
    ai_result = provider.respond(conversation_history=[], user_profile=_user_profile(user))

    ai_message = ChatMessage(
        user_id=user.id, session_id=session_id, role="ai", content=ai_result["message"]
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify(
        {
            "session_id": session_id,
            "message": ai_message.to_dict(),
            "topic": ai_result["topic"],
            "ready_for_analysis": ai_result["ready_for_analysis"],
        }
    ), 201


@chat_api.route("/message", methods=["POST"])
def send_message():
    """Send a user message and receive the next AI turn."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    session_id = data.get("session_id")
    content = (data.get("content") or "").strip()

    user = get_user_or_404(user_id)
    if not user:
        return error("Valid user_id is required.", 404)
    if not session_id:
        return error("session_id is required.")
    if not content:
        return error("content is required.")

    user_message = ChatMessage(user_id=user.id, session_id=session_id, role="user", content=content)
    db.session.add(user_message)
    db.session.commit()

    history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    ]

    provider = get_ai_provider(_current_provider_name())
    ai_result = provider.respond(conversation_history=history, user_profile=_user_profile(user))

    ai_message = ChatMessage(
        user_id=user.id, session_id=session_id, role="ai", content=ai_result["message"]
    )
    db.session.add(ai_message)
    db.session.commit()

    return jsonify(
        {
            "user_message": user_message.to_dict(),
            "ai_message": ai_message.to_dict(),
            "topic": ai_result["topic"],
            "ready_for_analysis": ai_result["ready_for_analysis"],
        }
    ), 201


@chat_api.route("/<session_id>/history", methods=["GET"])
def chat_history(session_id):
    messages = (
        ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
    )
    return jsonify([m.to_dict() for m in messages])


def _current_provider_name():
    from flask import current_app

    return current_app.config.get("AI_PROVIDER", "mock")


def _user_profile(user: User) -> dict:
    profile = {"name": user.name}
    if user.birth_detail:
        profile["moon_sign"] = user.birth_detail.moon_sign
        profile["sun_sign"] = user.birth_detail.sun_sign
    return profile


# ===========================================================================
# HEALING RECOMMENDATIONS
# ===========================================================================

@recommendations_api.route("/generate", methods=["POST"])
def generate_recs():
    """Analyzes a finished chat session and stores ranked recommendations."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    chat_session_id = data.get("session_id")

    user = get_user_or_404(user_id)
    if not user:
        return error("Valid user_id is required.", 404)
    if not chat_session_id:
        return error("session_id is required.")

    history = [
        {"role": m.role, "content": m.content}
        for m in ChatMessage.query.filter_by(session_id=chat_session_id).order_by(ChatMessage.created_at).all()
    ]
    if not history:
        return error("No conversation found for that session_id.", 404)

    ranked = generate_recommendations(history)

    # Replace any prior recommendations tied to this session so re-running
    # the analysis doesn't duplicate rows.
    Recommendation.query.filter_by(user_id=user.id, session_id=chat_session_id).delete()

    created = []
    for item in ranked:
        rec = Recommendation(user_id=user.id, session_id=chat_session_id, **item)
        db.session.add(rec)
        created.append(rec)

    db.session.commit()
    return jsonify([r.to_dict() for r in created]), 201


@recommendations_api.route("/user/<user_id>", methods=["GET"])
def user_recommendations(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)
    recs = Recommendation.query.filter_by(user_id=user.id).order_by(
        Recommendation.confidence_score.desc()
    ).all()
    return jsonify([r.to_dict() for r in recs])


@recommendations_api.route("/<rec_id>/save", methods=["POST"])
def toggle_save_recommendation(rec_id):
    rec = Recommendation.query.get(rec_id)
    if not rec:
        return error("Recommendation not found.", 404)
    rec.is_saved = not rec.is_saved
    db.session.commit()
    return jsonify(rec.to_dict())


# ===========================================================================
# EXPERTS / PRACTITIONERS + BOOKINGS
# ===========================================================================

@experts_api.route("", methods=["GET"])
def list_experts():
    modality = request.args.get("modality")
    query = Expert.query
    experts = query.all()
    if modality:
        experts = [e for e in experts if modality.lower() in [s.lower() for s in e.specialization]]
    return jsonify([e.to_dict() for e in experts])


@experts_api.route("/<expert_id>", methods=["GET"])
def get_expert(expert_id):
    expert = Expert.query.get(expert_id)
    if not expert:
        return error("Expert not found.", 404)
    return jsonify(expert.to_dict())


@experts_api.route("/<expert_id>/book", methods=["POST"])
def book_expert(expert_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    session_datetime = (data.get("session_datetime") or "").strip()

    user = get_user_or_404(user_id)
    expert = Expert.query.get(expert_id)
    if not user:
        return error("Valid user_id is required.", 404)
    if not expert:
        return error("Expert not found.", 404)
    if not session_datetime:
        return error("session_datetime is required.")

    booking = Booking(
        user_id=user.id, expert_id=expert.id, session_datetime=session_datetime, status="upcoming"
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify(booking.to_dict()), 201


@experts_api.route("/bookings/<user_id>", methods=["GET"])
def user_bookings(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)
    return jsonify([b.to_dict() for b in user.bookings])


# ===========================================================================
# JOURNAL
# ===========================================================================

@journal_api.route("", methods=["POST"])
def create_journal_entry():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    content = (data.get("content") or "").strip()
    mood = (data.get("mood") or "").strip() or None

    user = get_user_or_404(user_id)
    if not user:
        return error("Valid user_id is required.", 404)
    if not content:
        return error("content is required.")

    entry = JournalEntry(user_id=user.id, content=content, mood=mood)
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201


@journal_api.route("/user/<user_id>", methods=["GET"])
def list_journal_entries(user_id):
    user = get_user_or_404(user_id)
    if not user:
        return error("User not found.", 404)
    entries = JournalEntry.query.filter_by(user_id=user.id).order_by(
        JournalEntry.created_at.desc()
    ).all()
    return jsonify([e.to_dict() for e in entries])
