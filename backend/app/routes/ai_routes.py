from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Question, Answer, User, Category, STATUS_OPEN, QUESTION_STATUS_LABELS, ROLE_ADMIN, ROLE_MENTOR
from app.auth import get_current_user, require_role
from app.Services.ai_service import get_ai_chat_reply, AI_PROVIDER
from app.Services import gamification_service as gamify
from app.seed import AI_ASSISTANT_USERNAME

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def _get_ai_user(db: Session) -> User:
    ai_user = db.query(User).filter(User.Username == AI_ASSISTANT_USERNAME).first()
    if not ai_user:
        raise HTTPException(status_code=500, detail="AI Assistant system account is missing - restart the backend to reseed it.")
    return ai_user


def _serialize_ai_question(q: Question) -> dict:
    answer = q.answers[0] if q.answers else None
    return {
        "QuestionID": q.QuestionID,
        "Title": q.Title,
        "Description": q.Description,
        "AttachmentPath": q.AttachmentPath,
        "Status": QUESTION_STATUS_LABELS.get(q.StatusID, "Open"),
        "CreatedAt": q.CreatedAt,
        "AuthorName": q.user.FullName if q.user else None,
        "Answer": {
            "AnswerID": answer.AnswerID,
            "AnswerText": answer.AnswerText,
            "IsAccepted": answer.IsAccepted,
        } if answer else None,
    }


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    Message: str
    History: list[ChatTurn] = []
    ImageBase64: str | None = None  # raw base64, no data: prefix
    ImageMimeType: str | None = None


@router.post("/chat")
def chat(payload: ChatRequest, current_user=Depends(get_current_user)):
    """Live, ephemeral conversation with the AI Assistant - nothing is
    saved here, exactly like talking to any chatbot. Nobody wants every
    'hi' or throwaway question cluttering the Knowledge Base review
    queue, so persistence is a separate, deliberate step - see
    /ai/submit-for-review, triggered by the "Send for Mentor review"
    button on a specific answer the user actually wants kept."""

    history = [(turn.role, turn.content) for turn in payload.History]
    image = (
        {"base64": payload.ImageBase64, "mime_type": payload.ImageMimeType}
        if payload.ImageBase64 and payload.ImageMimeType
        else None
    )
    reply = get_ai_chat_reply(payload.Message, history, image=image)

    return {"Reply": reply, "Source": AI_PROVIDER if AI_PROVIDER != "none" else "unavailable"}


class SubmitForReviewRequest(BaseModel):
    Message: str
    AnswerText: str
    CategoryID: int | None = None
    AttachmentPath: str | None = None


@router.post("/submit-for-review")
def submit_for_review(payload: SubmitForReviewRequest, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Persists ONE specific chat exchange the user chose to keep: turns
    it into a real Question with the AI's already-generated reply
    attached as a normal Answer (authored by the AI Assistant system
    account, IsAIGenerated=True). It shows up in the normal Questions
    list, a mentor/admin can Accept it, and once accepted it enters the
    Knowledge Base - same pipeline as a human-answered question."""

    user = db.query(User).filter(User.UserID == current_user["UserID"], User.IsActive.is_(True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    category_id = payload.CategoryID
    if not category_id:
        general = db.query(Category).filter(Category.CategoryName == "General").first()
        category_id = general.CategoryID if general else db.query(Category).first().CategoryID

    title = payload.Message.strip()[:120]

    question = Question(
        UserID=user.UserID,
        CategoryID=category_id,
        StatusID=STATUS_OPEN,
        Title=title,
        Description=payload.Message,
        AttachmentPath=payload.AttachmentPath,
        Source="ai_assistant",
        ViewsCount=0,
    )
    db.add(question)
    db.flush()

    ai_user = _get_ai_user(db)
    answer = Answer(
        QuestionID=question.QuestionID,
        UserID=ai_user.UserID,
        AnswerText=payload.AnswerText,
        IsAIGenerated=True,
        IsAccepted=False,
        Upvotes=0,
    )
    db.add(answer)

    gamify.award_points(db, user, gamify.POINTS_ASK_QUESTION, reason="Submitted an AI answer for mentor review")

    db.commit()
    db.refresh(question)

    return _serialize_ai_question(question)


@router.get("/my-questions")
def my_ai_questions(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Every exchange this user has submitted for mentor review, newest
    first - only ones they deliberately chose to keep, not every message
    they sent the AI."""

    questions = (
        db.query(Question)
        .filter(Question.UserID == current_user["UserID"], Question.Source == "ai_assistant")
        .order_by(Question.CreatedAt.desc())
        .limit(50)
        .all()
    )
    return [_serialize_ai_question(q) for q in questions]


@router.get("/pending-review")
def pending_review(current_user=Depends(require_role(ROLE_ADMIN, ROLE_MENTOR)), db: Session = Depends(get_db)):
    """Mentor/Admin-only queue: every AI-generated answer, from any
    user, that hasn't been accepted yet. This is the dedicated review
    surface - instead of mentors having to stumble across AI-sourced
    questions while browsing the normal Questions list."""

    questions = (
        db.query(Question)
        .join(Answer, Answer.QuestionID == Question.QuestionID)
        .filter(
            Question.Source == "ai_assistant",
            Answer.IsAIGenerated.is_(True),
            Answer.IsAccepted.is_(False),
        )
        .order_by(Question.CreatedAt.asc())
        .distinct()
        .all()
    )
    return [_serialize_ai_question(q) for q in questions]
