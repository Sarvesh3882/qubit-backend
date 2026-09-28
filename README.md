# QUBIT — Backend

> AI-Based Interactive Quantum Algorithm Learning Platform — API Server

FastAPI backend powering the QUBIT quantum computing education platform. Provides authentication, curriculum management, quantum circuit simulation, AI tutoring, research intelligence, and more.

**Live API**: [qubit-backend-fbli.onrender.com/api/health](https://qubit-backend-fbli.onrender.com/api/health)  
**Frontend**: [qubit-henna.vercel.app](https://qubit-henna.vercel.app)  
**API Docs**: [qubit-backend-fbli.onrender.com/docs](https://qubit-backend-fbli.onrender.com/docs)

---

## Features

- **Auth** — JWT-based authentication with registration, login, and profile management
- **Curriculum** — Full quantum computing syllabus with learning paths, modules, and lessons
- **Progress Tracking** — Per-lesson completion, quiz submissions, XP, streaks, and badges
- **AI Tutor** — Mistral AI agent integration with RAG-based lesson context injection
- **Adaptive Learning** — Placement assessment, concept mastery tracking, personalised paths
- **Certification** — Auto-issued certificates with unique IDs on course completion
- **Quantum Simulation** — Qiskit Aer, PennyLane, QASM3 circuit execution backends
- **Algorithm Playground** — Gate-model and D-Wave simulated annealing
- **Research Intelligence** — arXiv, OpenAlex, Semantic Scholar, Crossref, GNews aggregation
- **Classroom** — Teacher + student management, assignments, progress visibility
- **Infrastructure** — Origin Quantum QPanda3 real QPU integration

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Language | Python 3.11+ |
| ORM | SQLModel + SQLAlchemy (async) |
| Database | SQLite (aiosqlite) / PostgreSQL-ready |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Simulation | Qiskit 2.x, Qiskit Aer, PennyLane |
| Annealing | D-Wave dimod, dwave-samplers |
| AI | Mistral AI (Agents API + Chat Completions) |
| QPU | Origin Quantum QPanda3 Runtime |
| HTTP | httpx (async) |

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/Sarvesh3882/qubit-backend.git
cd qubit-backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key — use a long random string |
| `DATABASE_URL` | ✅ | `sqlite+aiosqlite:///./qubit.db` (local) |
| `FRONTEND_ORIGIN` | ✅ | `http://localhost:3000` (local) |
| `MISTRAL_API_KEY` | Optional | AI tutor — get at [console.mistral.ai](https://console.mistral.ai) |
| `MISTRAL_AGENT_ID` | Optional | Mistral Agent ID for custom tutor persona |
| `GNEWS_API_KEY` | Optional | News feed — get at [gnews.io](https://gnews.io) |
| `OPENALEX_EMAIL` | Optional | Your email for OpenAlex polite pool |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional | Higher rate limits on S2 API |
| `QPANDA3_API_KEY` | Optional | Origin Quantum real QPU access |

### Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at [http://localhost:8000](http://localhost:8000)  
Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints

| Prefix | Description |
|--------|-------------|
| `/api/auth` | Register, login, profile |
| `/api/curriculum` | Learning paths, modules, lessons |
| `/api/progress` | Lesson completion, XP, streaks |
| `/api/agent` | AI tutor chat |
| `/api/assessment` | Placement test |
| `/api/adaptive` | Personalised learning |
| `/api/certification` | Issue + verify certificates |
| `/api/composer` | Circuit simulation |
| `/api/algorithms` | Algorithm playground |
| `/api/research` | Papers + news aggregation |
| `/api/classroom` | Teacher + student management |
| `/api/infrastructure` | QPU job submission |
| `/api/health` | Health check |

Full interactive docs at `/docs` (Swagger UI) or `/redoc`.

---

## Project Structure

```
app/
├── main.py               # FastAPI app + CORS + lifespan
├── api/                  # Route handlers
│   ├── auth.py
│   ├── curriculum.py
│   ├── progress.py
│   ├── agent.py
│   ├── assessment.py
│   ├── adaptive.py
│   ├── certification.py
│   ├── composer.py
│   ├── algorithms.py
│   ├── research.py
│   ├── classroom.py
│   └── infrastructure.py
├── core/
│   ├── config.py         # Pydantic settings (reads .env)
│   ├── database.py       # SQLAlchemy async engine
│   └── security.py       # JWT + password hashing
├── models/               # SQLModel table definitions
├── services/             # Business logic
│   ├── curriculum.py     # Lesson content
│   ├── mistral_agent.py  # AI tutor provider
│   └── research/         # Research aggregators
└── providers/            # Quantum backend adapters
    ├── local_aer.py      # Qiskit Aer
    ├── origin_quantum.py # QPanda3 QPU
    └── registry.py
```

---

## Deployment

Deployed on **Render** (free tier) with a persistent disk for SQLite.

### Environment Variables on Render

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Generate on Render dashboard |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/qubit.db` |
| `FRONTEND_ORIGIN` | `https://qubit-henna.vercel.app` |
| `MISTRAL_API_KEY` | Your key |
| + others | See `.env.example` |

### Persistent Disk

Mount a 1 GB disk at `/data` to keep `qubit.db` across deploys.

### Start Command

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Related

- [qubit-frontend](https://github.com/Sarvesh3882/qubit-frontend) — Next.js frontend

---

## License

MIT
