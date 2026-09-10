from fastapi import FastAPI

from app.routes import category_routes
from app.routes import user_routes
from app.routes import question_routes
from app.routes import answer_routes
from app.routes import vote_routes


app = FastAPI(
    title="SIMDAA SOLVO API",
    description="Doubt Clearance and Knowledge Sharing Platform",
    version="0.1.0"
)


# -------------------------
# API Routers
# -------------------------

app.include_router(
    category_routes.router
)

app.include_router(
    user_routes.router
)

app.include_router(
    question_routes.router
)

app.include_router(
    answer_routes.router
)

app.include_router(
    vote_routes.router
)

# -------------------------
# Home
# -------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to SIMDAA SOLVO",
        "tagline": "Ask. Solve. Share."
    }