"""
Aether — AI Conversation Service
------------------------------------------------
Defines a small provider interface (`AIProvider`) so the real model
backing Aether's guided conversation can be swapped by replacing ONE
file / class, without touching routes.py. Today only `MockAIProvider`
is implemented — it produces warm, structured, on-brand responses
without calling any external API, so the product works fully offline.

To plug in a real model later:
    1. Implement a new class with the same `respond()` signature
       (e.g. `AnthropicProvider`, `OpenAIProvider`, `GeminiProvider`).
    2. Register it in `PROVIDERS` below.
    3. Set AI_PROVIDER in the environment to select it.

Safety rules baked into every provider:
    - Never diagnoses a medical or mental-health condition.
    - Never claims certainty about astrology or healing outcomes.
    - Always nudges towards professional care when illness is mentioned.
"""

from abc import ABC, abstractmethod

# Topics the guided conversation gently moves through, in rough order.
# The mock provider uses this to decide what to ask next.
CONVERSATION_TOPICS = [
    "opening",       # "What brings you here today?"
    "career",
    "relationships",
    "stress",
    "sleep",
    "energy",
    "purpose",
    "patterns",       # recurring life patterns
    "childhood",      # childhood influences
    "challenges",     # current challenges
    "goals",
    "closing",
]

MEDICAL_KEYWORDS = [
    "diagnosed", "diagnosis", "disease", "illness", "cancer", "depression",
    "anxiety disorder", "medication", "suicidal", "suicide", "self-harm",
    "chronic pain", "surgery", "doctor said", "therapist said", "panic attack",
]

TOPIC_PROMPTS = {
    "opening": "What brings you here today? Take your time — there's no wrong answer.",
    "career": "How do you feel about where you are in your work or career right now?",
    "relationships": "How would you describe your closest relationships lately — supportive, strained, or somewhere in between?",
    "stress": "When stress shows up for you, where do you usually feel it — in your body, your mind, or both?",
    "sleep": "How has your sleep been recently? Restful, restless, or somewhere in between?",
    "energy": "Through the day, when does your energy feel highest, and when does it dip?",
    "purpose": "Do you feel a sense of purpose in your daily life right now, or is that something you're searching for?",
    "patterns": "Are there patterns you keep noticing repeat in your life — in relationships, decisions, or emotions?",
    "childhood": "Looking back, is there anything from your childhood that still quietly shapes how you move through the world?",
    "challenges": "What feels like the biggest challenge you're carrying at the moment?",
    "goals": "If this journey goes well, what would feel different for you a few months from now?",
    "closing": "Thank you for sharing all of this with me. I have a good sense of where you are — shall I put together your reflections?",
}

MEDICAL_REDIRECT = (
    "Thank you for trusting me with something so personal. I want to be "
    "honest with you: I'm not able to diagnose or treat medical or mental "
    "health conditions, and what you've described deserves care from a "
    "qualified doctor or licensed therapist. Please consider reaching out "
    "to one — alongside that, I'm glad to keep exploring the emotional and "
    "reflective side of what you're going through, if that feels helpful."
)


class AIProvider(ABC):
    """Common interface every AI backend must implement."""

    @abstractmethod
    def respond(self, conversation_history: list[dict], user_profile: dict | None = None) -> dict:
        """
        Args:
            conversation_history: list of {"role": "user"|"ai", "content": str}
                in chronological order, most recent last.
            user_profile: optional dict with name / birth-chart context.

        Returns:
            {
                "message": str,           # the AI's reply (markdown-friendly)
                "topic": str,             # which CONVERSATION_TOPICS stage this maps to
                "ready_for_analysis": bool  # True once enough signal is gathered
            }
        """
        raise NotImplementedError


class MockAIProvider(AIProvider):
    """
    Deterministic, rule-based provider. Walks through CONVERSATION_TOPICS
    one at a time, watches for medical/mental-health disclosures and
    redirects safely, and flags `ready_for_analysis` once the closing
    topic has been reached.
    """

    def respond(self, conversation_history: list[dict], user_profile: dict | None = None) -> dict:
        last_user_message = self._last_user_message(conversation_history)

        if last_user_message and self._mentions_medical_topic(last_user_message):
            return {
                "message": MEDICAL_REDIRECT,
                "topic": "safety_redirect",
                "ready_for_analysis": False,
            }

        topic_index = self._next_topic_index(conversation_history)
        topic = CONVERSATION_TOPICS[topic_index]
        message = TOPIC_PROMPTS[topic]

        # Warm, brief acknowledgement of what the user just shared, before
        # moving to the next topic prompt (skipped on the very first turn).
        if last_user_message:
            message = f"{self._acknowledge(last_user_message)}\n\n{message}"

        return {
            "message": message,
            "topic": topic,
            "ready_for_analysis": topic == "closing",
        }

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _last_user_message(history: list[dict]) -> str | None:
        for turn in reversed(history):
            if turn.get("role") == "user":
                return turn.get("content", "")
        return None

    @staticmethod
    def _mentions_medical_topic(text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in MEDICAL_KEYWORDS)

    @staticmethod
    def _next_topic_index(history: list[dict]) -> int:
        # Count how many AI turns have already happened (excluding safety
        # redirects, which don't advance the conversation) to decide the
        # next topic in sequence.
        ai_turns = [t for t in history if t.get("role") == "ai"]
        index = min(len(ai_turns), len(CONVERSATION_TOPICS) - 1)
        return index

    @staticmethod
    def _acknowledge(user_text: str) -> str:
        trimmed = user_text.strip()
        if len(trimmed) < 12:
            return "I hear you."
        return "Thank you for sharing that — it helps me understand you a little better."


PROVIDERS = {
    "mock": MockAIProvider,
    # "openai": OpenAIProvider,       # implement + register when ready
    # "anthropic": AnthropicProvider,
    # "gemini": GeminiProvider,
    # "grok": GrokProvider,
}


def get_ai_provider(name: str = "mock") -> AIProvider:
    """Factory returning an instantiated provider for the given name."""
    provider_cls = PROVIDERS.get(name, MockAIProvider)
    return provider_cls()
