import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from dotenv import load_dotenv

from app.database import Base, engine
from app.seed import run_seed
from app.routes.upload_routes import UPLOAD_DIR

from app.routes import (
    category_routes,
    user_routes,
    question_routes,
    answer_routes,
    vote_routes,
    comment_routes,
)
from app.routes.dashboard_routes import router as dashboard_router
from app.routes.auth_routes import router as auth_router
from app.routes.gamification_routes import router as gamification_router
from app.routes.notification_routes import router as notification_router
from app.routes.admin_routes import router as admin_router
from app.routes.ai_routes import router as ai_router
from app.routes.upload_routes import router as upload_router

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SIMDAA SOLVO API",
    description="Doubt Clearance and Knowledge Sharing Platform for Simdaa Technologies",
    version="1.0.0",
)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serves uploaded question/answer attachment images back at /uploads/<file>.
# IMPORTANT: this must be registered AFTER upload_router below, not before.
# Starlette matches routes in registration order, and a Mount matches its
# entire path prefix regardless of HTTP method - if it were registered
# first, it would intercept POST /uploads/ before the upload endpoint
# ever saw it, and return 405 Method Not Allowed (StaticFiles only
# understands GET/HEAD).


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    run_seed()


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(category_routes.router)
app.include_router(user_routes.router)
app.include_router(question_routes.router)
app.include_router(answer_routes.router)
app.include_router(vote_routes.router)
app.include_router(comment_routes.router)
app.include_router(dashboard_router)
app.include_router(gamification_router)
app.include_router(notification_router)
app.include_router(admin_router)
app.include_router(ai_router)
app.include_router(upload_router)

# Registered AFTER upload_router - see the comment above for why the order matters.
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Home"])
def home():
    return {
        "Application": "SIMDAA SOLVO API",
        "Version": "1.0.0",
        "Status": "Running",
        "Tagline": "Ask. Solve. Share.",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}
