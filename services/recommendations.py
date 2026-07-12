"""
Aether — Healing Recommendation Engine
------------------------------------------------
Turns a finished guided conversation into a ranked set of healing-modality
recommendations. The MVP uses transparent keyword/topic scoring (not a
black box) so every recommendation can honestly explain "why it fits" —
this keeps the product trustworthy even before a real ML model is wired in.
"""

MODALITIES = {
    "Reiki": {
        "keywords": ["tense", "tension", "stress", "overwhelmed", "anxious", "heavy", "burnout"],
        "benefits": [
            "Promotes deep relaxation",
            "May ease physical tension",
            "Supports emotional balance",
        ],
        "expected_experience": "A gentle, hands-off energy session in a calm, quiet space. Most people describe a warm, deeply relaxing feeling.",
        "session_duration": "45–60 minutes",
        "estimated_price": "$50–$80",
        "what_to_expect": "You'll lie down fully clothed while the practitioner works with subtle energy near or lightly on the body.",
    },
    "Sound Healing": {
        "keywords": ["sleep", "restless", "insomnia", "noise", "overthinking", "racing thoughts"],
        "benefits": [
            "Can support better sleep quality",
            "Encourages a meditative state",
            "Often described as deeply calming",
        ],
        "expected_experience": "Immersive tones from singing bowls, gongs, or chimes wash over you while you rest comfortably.",
        "session_duration": "45–75 minutes",
        "estimated_price": "$40–$70",
        "what_to_expect": "You'll lie down with eyes closed as layered sound frequencies play around you.",
    },
    "Breathwork": {
        "keywords": ["energy", "anxious", "panic", "stuck", "purpose", "motivation", "tired"],
        "benefits": [
            "May help regulate the nervous system",
            "Can increase feelings of clarity",
            "Supports emotional release",
        ],
        "expected_experience": "Guided breathing patterns designed to shift your state — some describe it as energising, others as cathartic.",
        "session_duration": "30–50 minutes",
        "estimated_price": "$30–$60",
        "what_to_expect": "You'll follow a practitioner-led breathing rhythm, seated or lying down.",
    },
    "Aura Cleansing": {
        "keywords": ["negative", "drained", "heavy energy", "unbalanced", "disconnected"],
        "benefits": [
            "Aims to support a sense of lightness",
            "Often paired with intention-setting",
            "May help with feeling emotionally 'stuck'",
        ],
        "expected_experience": "A calm, ritual-like session focused on clearing and re-aligning your personal energy field.",
        "session_duration": "30–45 minutes",
        "estimated_price": "$45–$75",
        "what_to_expect": "The practitioner works around your body using intention, breath, or light touch — no physical manipulation required.",
    },
    "Past Life Regression": {
        "keywords": ["pattern", "recurring", "childhood", "repeat", "familiar fear", "déjà vu"],
        "benefits": [
            "Explores recurring life patterns",
            "Can offer new perspective on longstanding fears",
            "Often described as insightful and reflective",
        ],
        "expected_experience": "A guided, hypnotherapy-style session exploring memories, imagery, and associations in a relaxed state.",
        "session_duration": "60–90 minutes",
        "estimated_price": "$70–$120",
        "what_to_expect": "You remain fully aware and in control throughout — this is guided reflection, not sleep or trance.",
    },
    "Meditation": {
        "keywords": ["purpose", "goal", "clarity", "focus", "calm", "grounded", "reflect"],
        "benefits": [
            "Builds a sustainable calm practice",
            "Supports self-awareness over time",
            "Backed by a broad body of wellness research",
        ],
        "expected_experience": "A guided sitting practice tailored to your current state — great as an ongoing, low-cost habit.",
        "session_duration": "20–30 minutes",
        "estimated_price": "$0–$25",
        "what_to_expect": "You'll sit comfortably while a guide leads you through breath and awareness techniques.",
    },
}


def _score_modality(name: str, config: dict, corpus: str) -> float:
    hits = sum(1 for kw in config["keywords"] if kw in corpus)
    base = 20.0 + hits * 18.0
    return min(base, 98.0)


def _stars_from_score(score: float) -> int:
    if score >= 85:
        return 5
    if score >= 65:
        return 4
    if score >= 45:
        return 3
    if score >= 25:
        return 2
    return 1


def generate_recommendations(conversation_history: list[dict]) -> list[dict]:
    """
    Score every modality against the full user-side conversation transcript
    and return a ranked list of recommendation dicts (highest confidence
    first), matching the Recommendation model's fields.
    """
    corpus = " ".join(
        turn.get("content", "").lower()
        for turn in conversation_history
        if turn.get("role") == "user"
    )

    results = []
    for name, config in MODALITIES.items():
        score = _score_modality(name, config, corpus)
        matched_keywords = [kw for kw in config["keywords"] if kw in corpus]

        if matched_keywords:
            why = (
                f"Based on what you shared — particularly around "
                f"{', '.join(matched_keywords[:2])} — {name} tends to be a "
                f"gentle, well-matched starting point."
            )
        else:
            why = (
                f"{name} is a well-rounded, low-risk practice that pairs "
                f"well with your overall reflections so far."
            )

        results.append(
            {
                "modality_name": name,
                "stars": _stars_from_score(score),
                "confidence_score": round(score, 1),
                "why_it_fits": why,
                "benefits": config["benefits"],
                "expected_experience": config["expected_experience"],
                "session_duration": config["session_duration"],
                "estimated_price": config["estimated_price"],
                "what_to_expect": config["what_to_expect"],
            }
        )

    results.sort(key=lambda r: r["confidence_score"], reverse=True)
    return results
