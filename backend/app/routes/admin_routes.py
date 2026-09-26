from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Question, Answer, Category, ROLE_ADMIN, STATUS_OPEN
from app.auth import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/analytics")
def analytics(current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    questions_per_category = (
        db.query(Category.CategoryName, func.count(Question.QuestionID))
        .outerjoin(Question, Question.CategoryID == Category.CategoryID)
        .filter(Category.IsActive.is_(True))
        .group_by(Category.CategoryName)
        .all()
    )

    top_askers = (
        db.query(User.FullName, func.count(Question.QuestionID).label("cnt"))
        .join(Question, Question.UserID == User.UserID)
        .group_by(User.FullName)
        .order_by(func.count(Question.QuestionID).desc())
        .limit(5)
        .all()
    )

    top_mentors = (
        db.query(User.FullName, func.count(Answer.AnswerID).label("cnt"))
        .join(Answer, Answer.UserID == User.UserID)
        .filter(Answer.IsAccepted.is_(True))
        .group_by(User.FullName)
        .order_by(func.count(Answer.AnswerID).desc())
        .limit(5)
        .all()
    )

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    questions_last_30_days = db.query(Question).filter(Question.CreatedAt >= thirty_days_ago).count()

    unanswered_open_questions = (
        db.query(Question)
        .filter(Question.StatusID == STATUS_OPEN)
        .filter(~Question.answers.any())
        .count()
    )

    return {
        "QuestionsPerCategory": [{"Category": c, "Count": n} for c, n in questions_per_category],
        "TopAskers": [{"FullName": n, "Count": c} for n, c in top_askers],
        "TopMentors": [{"FullName": n, "Count": c} for n, c in top_mentors],
        "QuestionsLast30Days": questions_last_30_days,
        "UnansweredOpenQuestions": unanswered_open_questions,
        "TotalUsers": db.query(User).count(),
        "ActiveUsers": db.query(User).filter(User.IsActive.is_(True)).count(),
    }


@router.get("/reports/unanswered")
def unanswered_report(current_user=Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    questions = (
        db.query(Question)
        .filter(Question.StatusID == STATUS_OPEN)
        .filter(~Question.answers.any())
        .order_by(Question.CreatedAt.asc())
        .all()
    )
    return [
        {
            "QuestionID": q.QuestionID,
            "Title": q.Title,
            "AuthorName": q.user.FullName if q.user else None,
            "CategoryName": q.category.CategoryName if q.category else None,
            "CreatedAt": q.CreatedAt,
            "DaysOpen": (datetime.utcnow() - q.CreatedAt).days,
        }
        for q in questions
    ]
