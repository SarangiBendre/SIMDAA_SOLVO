from fastapi import APIRouter, Depends
from sqlalchemy import text

from ..database import engine
from ..auth import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


@router.get("/stats")
def get_dashboard_stats():

    with engine.connect() as connection:

        total_users = connection.execute(
            text("SELECT COUNT(*) FROM Users")
        ).scalar()

        total_questions = connection.execute(
            text("SELECT COUNT(*) FROM Questions")
        ).scalar()

        total_answers = connection.execute(
            text("SELECT COUNT(*) FROM Answers")
        ).scalar()

        total_categories = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM Categories
                WHERE IsActive = 1
            """)
        ).scalar()

        accepted_answers = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM Answers
                WHERE IsAccepted = 1
            """)
        ).scalar()

        return {
            "TotalUsers": total_users,
            "TotalQuestions": total_questions,
            "TotalAnswers": total_answers,
            "TotalCategories": total_categories,
            "AcceptedAnswers": accepted_answers
        }