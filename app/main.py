from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api import auth, curriculum, progress, composer, code_runner, algorithms, agent, infrastructure
from app.api import assessment, adaptive, certification
from app.api import research, news
from app.api import classroom

# Import new models so SQLModel.metadata.create_all() picks them up at startup
import app.models.adaptive  # noqa: F401 — registers PlacementAssessment, Certificate
import app.models.research   # noqa: F401 — registers ResearchItem, NewsItem cache tables
import app.models.classroom  # noqa: F401 — registers Classroom, ClassMembership, ClassAssignment
from app.api.adaptive import ConceptAnswer  # noqa: F401 — registers concept_answers table
from app.models.progress import QuizSubmission  # noqa: F401 — registers quiz_submissions table


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="QUBIT API",
    description="AI-Based Interactive Quantum Algorithm Learning Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# FRONTEND_ORIGIN may be a comma-separated list of allowed origins, e.g.:
#   "https://qubit-app.vercel.app,https://qubit-app-git-main-user.vercel.app"
# Always include localhost for local development.
_raw_origins = settings.FRONTEND_ORIGIN or ""
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
_allowed_origins += ["http://localhost:3000", "http://localhost:3001"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # all Vercel preview deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(curriculum.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(composer.router, prefix="/api")
app.include_router(code_runner.router, prefix="/api")
app.include_router(algorithms.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(infrastructure.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
app.include_router(adaptive.router, prefix="/api")
app.include_router(certification.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(classroom.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "QUBIT API"}
