# SIMDAA SOLVO

**Ask. Solve. Share.** The internal doubt-clearance and knowledge-sharing
platform for Simdaa Technologies.

Students/trainees ask questions, mentors answer them, a lightweight AI
Assistant + Knowledge Base search surfaces similar solved questions before
a duplicate gets posted, and a points/badges system rewards participation.

---

## What's included

- **Frontend**: React + Vite, corporate SIMDAA theme, fully redesigned pages
  (Dashboard, Questions, Ask Question, Knowledge Base, AI Assistant,
  Question Details, Leaderboard, Notifications, Profile, Admin: Users /
  Categories / Analytics)
- **Backend**: FastAPI + SQLAlchemy, JWT auth, SQLite by default (no external
  DB setup needed) - one env var away from PostgreSQL / SQL Server
- **Knowledge Base + Smart Search + AI Assistant**: three separate but
  related capabilities:
  - *Smart Search*: as you type a new question, a similarity engine
    surfaces related solved questions before you post a duplicate.
  - *Knowledge Base*: a dedicated, always-browsable page of every solved
    question - organizational memory that grows over time.
  - *AI Assistant*: ask it anything (with an optional image attachment)
    and it gives an instant AI-generated answer. Unlike a normal chat
    widget, every question you ask is **persisted** - it survives tab
    changes, refreshes, and logging back in later - and shows up as a
    normal question that any Mentor or Admin can review. Once a mentor
    accepts the AI's answer, it becomes a real accepted answer and
    enters the Knowledge Base exactly like a human-answered question.
    Works with a built-in fallback with zero setup; set `AI_PROVIDER`
    in `backend/.env` to connect a real LLM (OpenAI, Gemini, or a
    self-hosted Ollama).
- **Gamification**: points, levels, auto-awarded badges. The leaderboard
  shows only the CURRENT month's points and resets to zero every month;
  past months are frozen and browsable any time via the month picker.
  Deleting a question/answer reverses the points it earned.
- **Notifications**: in-app + email (Brevo/SMTP), best-effort so the app
  never breaks if email isn't configured. New questions email every
  active user; a new answer emails just the question's author.
- **Full account self-service**: edit/delete your own questions,
  answers, and comments; change your password from Profile; reset a
  forgotten password by username (not email - the code goes to the
  email already on file, shown back only in masked form).
- **Attachments**: attach a screenshot or image to a question, an
  answer, or an AI Assistant message (used as vision input for
  OpenAI/Gemini, or an Ollama vision model like llava).
- **Admin dashboard**: user/category management (including permanently
  deleting an account, not just deactivating it), analytics,
  unanswered-question report.

---

## Quick start (local development)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit values as needed (defaults work out of the box)
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000` (Swagger docs at `/docs`). On first
run it automatically creates the SQLite database and seeds:

- Roles (Admin, Mentor/Senior, Employee, Intern, Trainee)
- A default admin account: **username `admin`, password `Admin@123`**
  (change `DEFAULT_ADMIN_PASSWORD` in `.env` before first run in production,
  or change the password after logging in)
- Starter categories and the badge catalog

> Using SQL Server instead? Set `DATABASE_URL` in `.env` (see the example
> in `.env.example`) and `pip install -r requirements-mssql.txt`. You'll
> also need the "ODBC Driver 17 for SQL Server" installed on the machine.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env              # set VITE_API_URL if the backend isn't local
npm run dev
```

Runs at `http://localhost:5173`.

---

## Deploying

### Docker (backend)

```bash
cd backend
docker build -t simdaa-solvo-api .
docker run -p 8000:8000 --env-file .env simdaa-solvo-api
```

Mount a volume if you want the SQLite file to persist across container
restarts, or point `DATABASE_URL` at a managed Postgres/SQL Server instance.

### Frontend

```bash
cd frontend
npm run build
```

This produces a static `dist/` folder - deploy it to any static host
(Netlify, Vercel, S3 + CloudFront, nginx, etc.) and set `VITE_API_URL` at
build time to your deployed backend's URL.

---

## Environment variables

See `backend/.env.example` and `frontend/.env.example` for the full list.
Key ones:

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | SQLite (default), Postgres, or SQL Server connection string |
| `JWT_SECRET_KEY` | backend | **Change this before deploying anywhere real** |
| `CORS_ORIGINS` | backend | Comma-separated list of allowed frontend origins |
| `SMTP_*` / `EMAIL_*` | backend | Email notifications (optional, best-effort) |
| `OLLAMA_ENABLED` / `OLLAMA_HOST` | backend | Optional local LLM for the AI Assistant |
| `VITE_API_URL` | frontend | Where the frontend should call the API |

---

## Project structure

```text
backend/
  app/
    main.py            FastAPI app + router wiring + startup seeding
    database.py         SQLAlchemy engine/session (portable DB config)
    models.py            ORM models
    auth.py               JWT + password hashing
    seed.py                First-run seed data
    Services/
      email_service.py      Best-effort SMTP notifications
      ai_service.py           Knowledge Base similarity + AI suggestion
      gamification_service.py Points, levels, badges
    routes/                 One file per resource (questions, answers, ...)

frontend/
  src/
    api/client.js         Axios instance with auth interceptor
    context/AuthContext.jsx
    components/            Sidebar, Topbar, cards, route guards
    pages/                  One file per screen
    styles/                 Design tokens + per-page styles
```

---

## Notes / known limitations

- All dates in the UI display as `DD-MM-YYYY` (with 24-hour time where a
  timestamp is shown), regardless of the browser's locale.
- Smart Search and the AI Assistant both fall back to a dependency-free
  keyword-similarity engine with zero setup. Set `AI_PROVIDER=openai`,
  `gemini`, or `ollama` in `backend/.env` (plus the matching API key) to
  get real LLM-generated answers instead.
- Email sending is best-effort: if SMTP isn't configured or reachable, the
  app logs a warning and continues rather than failing the request.
