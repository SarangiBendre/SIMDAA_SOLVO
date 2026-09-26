from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.database import get_db
from app.models import Question, Category, User, Answer, Notification, QuestionView, STATUS_OPEN, STATUS_ANSWERED, QUESTION_STATUS_LABELS
from app.auth import get_current_user
from app.Services.email_service import send_email
from app.Services.ai_service import rank_similar_questions, get_ai_suggestion
from app.Services import gamification_service as gamify

router = APIRouter(prefix="/questions", tags=["Questions"])


class QuestionCreate(BaseModel):
    CategoryID: int
    Title: str
    Description: str
    AttachmentPath: str | None = None


class QuestionUpdate(BaseModel):
    CategoryID: int | None = None
    Title: str | None = None
    Description: str | None = None
    AttachmentPath: str | None = None


class SuggestRequest(BaseModel):
    Title: str
    Description: str = ""


def _serialize(q: Question, include_author=True):
    data = {
        "QuestionID": q.QuestionID,
        "UserID": q.UserID,
        "CategoryID": q.CategoryID,
        "CategoryName": q.category.CategoryName if q.category else None,
        "StatusID": q.StatusID,
        "Status": QUESTION_STATUS_LABELS.get(q.StatusID, "Open"),
        "Title": q.Title,
        "Description": q.Description,
        "AttachmentPath": q.AttachmentPath,
        "Source": q.Source,
        "ViewsCount": q.ViewsCount,
        "AnswersCount": len(q.answers),
        "CreatedAt": q.CreatedAt,
        "UpdatedAt": q.UpdatedAt,
    }
    if include_author and q.user:
        data["AuthorName"] = q.user.FullName
    return data


# ============================================================
# GET /questions/  (supports ?category_id=&status=&mine=)
# ============================================================

@router.get("/")
def get_questions(category_id: int | None = None, status: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Question)
    if category_id:
        query = query.filter(Question.CategoryID == category_id)
    if status:
        query = query.filter(Question.StatusID == status)

    questions = query.order_by(Question.CreatedAt.desc()).all()
    return [_serialize(q) for q in questions]


# ============================================================
# GET /questions/search?keyword=
# Simple substring search (fast path, used by the search bar)
# ============================================================

@router.get("/search")
def search_questions(keyword: str, db: Session = Depends(get_db)):
    like = f"%{keyword}%"
    questions = (
        db.query(Question)
        .filter(or_(Question.Title.ilike(like), Question.Description.ilike(like)))
        .order_by(Question.CreatedAt.desc())
        .all()
    )
    return [_serialize(q) for q in questions]


# ============================================================
# POST /questions/suggest
# Knowledge Base + AI Assistant: call this BEFORE posting a new
# question. Returns similar already-solved questions and a suggested
# answer, so duplicate questions can be avoided.
# ============================================================

@router.post("/suggest")
def suggest_before_posting(payload: SuggestRequest, db: Session = Depends(get_db)):
    all_questions = db.query(Question).order_by(Question.CreatedAt.desc()).limit(500).all()

    candidates = []
    for q in all_questions:
        accepted = next((a for a in q.answers if a.IsAccepted), None)
        candidates.append({
            "QuestionID": q.QuestionID,
            "Title": q.Title,
            "Description": q.Description,
            "Status": QUESTION_STATUS_LABELS.get(q.StatusID, "Open"),
            "AcceptedAnswerText": accepted.AnswerText if accepted else None,
        })

    top_matches = rank_similar_questions(payload.Title, payload.Description, candidates)
    ai_result = get_ai_suggestion(payload.Title, payload.Description, top_matches)

    return {
        "RelatedQuestions": [
            {k: v for k, v in m.items() if k != "AcceptedAnswerText"}
            for m in top_matches
        ],
        "AISuggestion": ai_result["suggestion"],
        "AISource": ai_result["source"],
    }


# ============================================================
# POST /questions/
# ============================================================

@router.post("/")
def create_question(question: QuestionCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == current_user["UserID"], User.IsActive.is_(True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    category = db.query(Category).filter(Category.CategoryID == question.CategoryID, Category.IsActive.is_(True)).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    new_question = Question(
        UserID=user.UserID,
        CategoryID=question.CategoryID,
        StatusID=STATUS_OPEN,
        Title=question.Title,
        Description=question.Description,
        AttachmentPath=question.AttachmentPath,
        ViewsCount=0,
    )
    db.add(new_question)

    gamify.award_points(db, user, gamify.POINTS_ASK_QUESTION, reason="Asked a question")

    already_asked = db.query(Question).filter(Question.UserID == user.UserID).count()
    if already_asked == 0:
        gamify.award_badge_manual(db, user, "First Question")

    db.commit()
    db.refresh(new_question)

    # Notify every other active user in the system (in-app always; email best-effort)
    notify_targets = (
        db.query(User)
        .filter(User.IsActive.is_(True), User.UserID != user.UserID)
        .all()
    )
    for target in notify_targets:
        db.add(Notification(
            UserID=target.UserID,
            Type="new_question",
            Message=f"New question posted: \"{new_question.Title}\"",
            Link=f"/questions/{new_question.QuestionID}",
        ))
        send_email(
            target.Email,
            "New Question Posted - SIMDAA SOLVO",
            f"A new question has been posted.\n\nTitle:\n{new_question.Title}\n\n"
            f"Description:\n{new_question.Description}\n\n"
            "Please log in to SIMDAA SOLVO to view and answer.\n\nRegards,\nSIMDAA SOLVO Team",
        )
    db.commit()

    return {"message": "Question created successfully", **_serialize(new_question)}


# ============================================================
# GET /questions/{question_id}/details
# ============================================================

@router.get("/{question_id}/details")
def get_question_details(question_id: int, db: Session = Depends(get_db)):
    # NOTE: this is a GET (read-only) endpoint on purpose. It used to bump
    # ViewsCount here, but a GET can be called many times per visit (React
    # StrictMode double-invokes effects in dev, refreshes, retries, etc.),
    # which inflated the count. View counting now lives in its own POST
    # endpoint below, called once per visitor per session by the frontend.
    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answers = sorted(question.answers, key=lambda a: (not a.IsAccepted, -a.Upvotes, a.CreatedAt))

    return {
        **_serialize(question),
        "Answers": [
            {
                "AnswerID": a.AnswerID,
                "UserID": a.UserID,
                "AuthorName": a.user.FullName if a.user else None,
                "AnswerText": a.AnswerText,
                "AttachmentPath": a.AttachmentPath,
                "IsAccepted": a.IsAccepted,
                "Upvotes": a.Upvotes,
                "CreatedAt": a.CreatedAt,
                "UpdatedAt": a.UpdatedAt,
                "CommentsCount": len(a.comments),
            }
            for a in answers
        ],
    }


@router.post("/{question_id}/view")
def record_view(question_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Records a view for the current logged-in user and increments the
    counter only the first time THIS user views THIS question - tracked
    server-side (question_views table) rather than via a browser-side
    flag, so it works correctly across devices, browser sessions, and
    multiple users testing from the same browser tab."""

    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    already_viewed = (
        db.query(QuestionView)
        .filter(QuestionView.QuestionID == question_id, QuestionView.UserID == current_user["UserID"])
        .first()
    )

    if not already_viewed:
        try:
            db.add(QuestionView(QuestionID=question_id, UserID=current_user["UserID"]))
            question.ViewsCount = (question.ViewsCount or 0) + 1
            db.commit()
        except IntegrityError:
            # Two requests for the same user/question landed at the same
            # time (e.g. React StrictMode firing an effect twice in dev)
            # and both passed the check above before either committed.
            # The unique constraint on (QuestionID, UserID) caught the
            # duplicate - that's exactly what it's there to prevent, so
            # just back off instead of crashing the request.
            db.rollback()
            db.refresh(question)

    return {"ViewsCount": question.ViewsCount}


@router.get("/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return _serialize(question)


@router.put("/{question_id}")
def update_question(question_id: int, payload: QuestionUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.QuestionID == question_id, Question.UserID == current_user["UserID"]).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if payload.Title is not None:
        question.Title = payload.Title
    if payload.Description is not None:
        question.Description = payload.Description
    if payload.CategoryID is not None:
        question.CategoryID = payload.CategoryID
    if payload.AttachmentPath is not None:
        question.AttachmentPath = payload.AttachmentPath

    db.commit()
    return {"message": "Question updated successfully"}


@router.delete("/{question_id}")
def delete_question(question_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.QuestionID == question_id, Question.UserID == current_user["UserID"]).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    asker = db.query(User).filter(User.UserID == current_user["UserID"]).first()
    if asker:
        gamify.deduct_points(db, asker, gamify.POINTS_ASK_QUESTION, reason="Question deleted")

    db.delete(question)
    db.commit()
    return {"message": "Question deleted successfully"}
