from fastapi import FastAPI

from app.routes import category_routes
from app.routes import user_routes
from app.routes import question_routes
from app.routes import answer_routes
from app.routes import vote_routes
from app.routes import comment_routes

from app.routes.dashboard_routes import router as dashboard_router
from app.routes.auth_routes import router as auth_router


app = FastAPI(
    title="SIMDAA SOLVO API",
    description="Doubt Clearance and Knowledge Sharing Platform",
    version="1.0.0"
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(category_routes.router)
app.include_router(user_routes.router)
app.include_router(question_routes.router)
app.include_router(answer_routes.router)
app.include_router(vote_routes.router)
app.include_router(comment_routes.router)

app.include_router(dashboard_router)
app.include_router(auth_router)


# ============================================================
# HOME
# ============================================================

@app.get(
    "/",
    tags=["Home"]
)
def home():

    return {
        "Application": "SIMDAA SOLVO API",
        "Version": "1.0.0",
        "Status": "Running",
        "Tagline": "Ask. Solve. Share."
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["System"]
)
def health_check():

    return {
        "status": "healthy"
    }