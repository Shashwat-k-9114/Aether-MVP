# Aether — Backend

> *Reconnect with yourself through guided wisdom.*

Aether is an AI-guided alternate-healing exploration platform. This
repository currently contains the **complete backend** (Flask + SQLite):
onboarding, mock Janampatri generation, a guided AI conversation engine,
a transparent healing-recommendation engine, a practitioner marketplace
with bookings, and a personal journal. The frontend (Three.js / GSAP
landing page, chat UI, dashboard) is the next build phase and will render
through the templates already wired up in `routes.py`.

**Aether does not diagnose medical or mental health conditions and does
not replace professional care.** The AI conversation engine actively
redirects to professional help whenever illness is mentioned — see
`services/ai.py`.

---

## Tech Stack

- Python 3.11+, Flask 3
- Flask-SQLAlchemy + SQLite (swap `DATABASE_URL` for Postgres in production)
- No frontend framework — vanilla HTML/CSS/JS + Three.js + GSAP (next phase)

## Folder Structure

```
aether/
├── app.py                 # application factory + entrypoint
├── config.py               # environment-based configuration
├── database.py              # SQLAlchemy instance + init/seed
├── models.py                 # User, BirthDetail, ChatMessage, Recommendation,
│                              # Expert, Booking, JournalEntry
├── routes.py                  # all Flask routes (page + REST API), in blueprints
├── services/
│   ├── ai.py                    # AI provider interface + MockAIProvider
│   ├── janampatri.py             # deterministic mock birth-chart generator
│   └── recommendations.py         # healing-modality scoring engine
├── utils/
│   └── helpers.py                  # validators + mock practitioner seed data
├── static/{css,js,images,fonts,icons,shaders}/   # frontend assets (next phase)
├── templates/                       # Jinja pages (placeholder stubs today)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Installation

```bash
git clone <repo-url> aether && cd aether
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit values as needed
```

## Running Locally

```bash
python app.py
# or
export FLASK_APP=app.py FLASK_ENV=development
flask run
```

The API is served at `http://127.0.0.1:5000`. On first run, SQLite tables
are created automatically and the practitioner marketplace is seeded with
mock experts (`database.py` → `_seed_experts_if_empty`).

Health check: `GET /health`

## Environment Variables

See `.env.example`. Key ones:

| Variable       | Purpose                                                             |
|----------------|----------------------------------------------------------------------|
| `SECRET_KEY`   | Flask session signing key                                             |
| `DATABASE_URL` | SQLAlchemy connection string (defaults to local SQLite)                |
| `AI_PROVIDER`  | `mock` today; set to `openai`/`anthropic`/`gemini`/`grok` once wired up |
| `AI_API_KEY`   | Credential for the active AI provider (unused by `mock`)                |

## API Overview

| Method | Route                                   | Purpose                                      |
|--------|------------------------------------------|-----------------------------------------------|
| POST   | `/api/users`                              | Create/find a user (name, email, gender)        |
| GET    | `/api/users/<id>`                          | Fetch a user                                     |
| POST   | `/api/users/<id>/birth-details`             | Submit DOB/time/place → generates Janampatri       |
| GET    | `/api/users/<id>/janampatri`                 | Fetch the generated chart                            |
| GET    | `/api/users/<id>/dashboard`                   | Aggregated dashboard summary                          |
| POST   | `/api/chat/start`                              | Begin a guided conversation session                     |
| POST   | `/api/chat/message`                             | Send a user message, get the AI's next turn               |
| GET    | `/api/chat/<session_id>/history`                 | Full transcript of a session                                |
| POST   | `/api/recommendations/generate`                   | Analyze a session → ranked healing recommendations             |
| GET    | `/api/recommendations/user/<id>`                   | All recommendations for a user                                   |
| POST   | `/api/recommendations/<id>/save`                    | Toggle "saved" on a recommendation                                 |
| GET    | `/api/experts`                                       | List practitioners (optional `?modality=` filter)                    |
| GET    | `/api/experts/<id>`                                   | Single practitioner                                                     |
| POST   | `/api/experts/<id>/book`                               | Book a session                                                            |
| GET    | `/api/experts/bookings/<user_id>`                        | A user's bookings                                                           |
| POST   | `/api/journal`                                             | Create a journal entry                                                       |
| GET    | `/api/journal/user/<id>`                                     | A user's journal entries                                                       |

All endpoints return JSON and standard HTTP status codes; validation
errors return `{"error": "..."}` with a `400`.

## AI Provider Architecture

`services/ai.py` defines an abstract `AIProvider` with one method,
`respond(conversation_history, user_profile)`. Today only
`MockAIProvider` exists — it walks a fixed set of reflective topics
(career, relationships, stress, sleep, energy, purpose, patterns,
childhood, challenges, goals) and detects medical/mental-health keywords
to safely redirect to professional care. To add a real model:

1. Implement a new class in `services/ai.py` with the same signature.
2. Register it in the `PROVIDERS` dict.
3. Set `AI_PROVIDER` in `.env` to select it — no route changes needed.

## Deployment on Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, pointing at the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn "app:create_app()"`
5. Add the environment variables from `.env.example` in Render's dashboard.
6. For production, attach a managed Postgres instance and set
   `DATABASE_URL` accordingly (SQLite is fine for demos but not for
   Render's ephemeral filesystem).

## Future Improvements

- Real AI provider integration (Anthropic/OpenAI/Gemini) behind the existing interface
- Real ephemeris-based Janampatri calculation (e.g. `pyswisseph`)
- Auth (magic-link or OAuth) instead of email-only identification
- Full frontend: Three.js hero, GSAP scroll reveals, glassmorphic chat UI, dashboard analytics
- Streaming AI responses (SSE) for a real-time typing effect
- Payments for practitioner bookings
