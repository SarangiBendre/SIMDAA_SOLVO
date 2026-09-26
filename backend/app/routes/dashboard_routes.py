from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Question, Answer, Category
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/me")
def me(user=Depends(get_current_user)):
    return user


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    return {
        "TotalUsers": db.query(User).count(),
        "TotalQuestions": db.query(Question).count(),
        "TotalAnswers": db.query(Answer).count(),
        "TotalCategories": db.query(Category).filter(Category.IsActive.is_(True)).count(),
        "AcceptedAnswers": db.query(Answer).filter(Answer.IsAccepted.is_(True)).count(),
    }


@router.get("/summary")
def get_dashboard_summary(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """One call that feeds the whole Dashboard page: stats + recent
    questions + the current user's own profile snapshot."""

    user = db.query(User).filter(User.UserID == current_user["UserID"]).first()

    recent_questions = (
        db.query(Question).order_by(Question.CreatedAt.desc()).limit(6).all()
    )

    my_questions = db.query(Question).filter(Question.UserID == current_user["UserID"]).count()
    my_answers = db.query(Answer).filter(Answer.UserID == current_user["UserID"]).count()
    my_accepted = db.query(Answer).filter(
        Answer.UserID == current_user["UserID"], Answer.IsAccepted.is_(True)
    ).count()

    return {
        "Stats": {
            "TotalUsers": db.query(User).count(),
            "TotalQuestions": db.query(Question).count(),
            "TotalAnswers": db.query(Answer).count(),
            "AcceptedAnswers": db.query(Answer).filter(Answer.IsAccepted.is_(True)).count(),
        },
        "Me": {
            "FullName": user.FullName if user else None,
            "Points": user.Points if user else 0,
            "Level": user.Level if user else "Beginner",
            "QuestionsAsked": my_questions,
            "AnswersPosted": my_answers,
            "AcceptedAnswers": my_accepted,
        },
        "RecentQuestions": [
            {
                "QuestionID": q.QuestionID,
                "Title": q.Title,
                "CategoryName": q.category.CategoryName if q.category else None,
                "AuthorName": q.user.FullName if q.user else None,
                "AnswersCount": len(q.answers),
                "CreatedAt": q.CreatedAt,
            }
            for q in recent_questions
        ],
    }
