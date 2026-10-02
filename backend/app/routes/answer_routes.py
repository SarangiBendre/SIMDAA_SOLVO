from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Answer, Question, User, Vote, Notification, STATUS_ANSWERED, ROLE_ADMIN, ROLE_MENTOR
from app.auth import get_current_user
from app.Services.email_service import send_email
from app.Services import gamification_service as gamify

router = APIRouter(prefix="/answers", tags=["Answers"])


def _email_everyone_about_answer(recipient_emails: list[str], answerer_name: str, question_title: str, answer_text: str):
    """Runs after the response is sent (see BackgroundTasks below) so
    posting an answer doesn't sit there waiting on N sequential email
    API calls before the answerer gets their response back. One
    recipient failing (bad address, provider hiccup) is logged and
    skipped rather than blocking the rest."""
    import logging
    logger = logging.getLogger("simdaa.email")

    for email in recipient_emails:
        try:
            send_email(
                email,
                "New answer posted - SIMDAA SOLVO",
                f"{answerer_name} answered \"{question_title}\".\n\n"
                f"Answer:\n{answer_text}\n\nLog in to SIMDAA SOLVO to view it.",
            )
        except Exception as exc:
            logger.warning("Could not email %s about new answer: %s", email, exc)


class AnswerCreate(BaseModel):
    QuestionID: int
    AnswerText: str
    AttachmentPath: str | None = None


class AnswerUpdate(BaseModel):
    AnswerText: str
    AttachmentPath: str | None = None


def _serialize(a: Answer):
    return {
        "AnswerID": a.AnswerID,
        "QuestionID": a.QuestionID,
        "UserID": a.UserID,
        "AuthorName": a.user.FullName if a.user else None,
        "AnswerText": a.AnswerText,
        "AttachmentPath": a.AttachmentPath,
        "IsAIGenerated": a.IsAIGenerated,
        "IsAccepted": a.IsAccepted,
        "Upvotes": a.Upvotes,
        "CreatedAt": a.CreatedAt,
        "UpdatedAt": a.UpdatedAt,
    }


@router.post("/")
def create_answer(answer: AnswerCreate, background_tasks: BackgroundTasks, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    question = db.query(Question).filter(Question.QuestionID == answer.QuestionID).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    user = db.query(User).filter(User.UserID == current_user["UserID"], User.IsActive.is_(True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    # "First Answer" badge now means first answer THIS MONTH (badges
    # reset monthly, same as points) - so this counts only this month's
    # answers, not all-time.
    already_answered = db.query(Answer).filter(
        Answer.UserID == user.UserID,
        Answer.CreatedAt >= gamify.current_month_start(),
    ).count()

    new_answer = Answer(
        QuestionID=answer.QuestionID,
        UserID=user.UserID,
        AnswerText=answer.AnswerText,
        AttachmentPath=answer.AttachmentPath,
        IsAccepted=False,
        Upvotes=0,
    )
    db.add(new_answer)

    gamify.award_points(db, user, gamify.POINTS_ANSWER_QUESTION, reason="Answered a question")

    # See the matching comment in question_routes.py's create_question -
    # same autoflush pitfall, same fix: count before adding, not after.
    if already_answered == 0:
        gamify.award_badge_manual(db, user, "First Answer")

    db.commit()
    db.refresh(new_answer)

    # In-app notifications: everyone gets alerted (matches how a new
    # question already notifies everyone) - the asker gets a message
    # naming it as *their* question specifically, everyone else gets
    # the general "new answer posted" version.
    notify_targets = (
        db.query(User)
        .filter(User.IsActive.is_(True), User.UserID != user.UserID)
        .all()
    )
    for target in notify_targets:
        is_asker = target.UserID == question.UserID
        db.add(Notification(
            UserID=target.UserID,
            Type="new_answer",
            Message=(
                f"{user.FullName} answered your question \"{question.Title}\""
                if is_asker else
                f"{user.FullName} answered \"{question.Title}\""
            ),
            Link=f"/questions/{question.QuestionID}",
        ))
    db.commit()

    # Manager's call: alert everyone (not just the question's asker) by
    # email whenever anyone answers any question, so the whole team sees
    # activity as it happens rather than just the one person involved.
    recipient_emails = [u.Email for u in notify_targets if u.Email]
    background_tasks.add_task(_email_everyone_about_answer, recipient_emails, user.FullName, question.Title, new_answer.AnswerText)

    return {"message": "Answer created successfully", **_serialize(new_answer)}


@router.get("/question/{question_id}")
def get_answers_by_question(question_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    question = db.query(Question).filter(Question.QuestionID == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answers = sorted(question.answers, key=lambda a: (not a.IsAccepted, -a.Upvotes, a.CreatedAt))
    return [_serialize(a) for a in answers]


@router.get("/{answer_id}")
def get_answer(answer_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    return _serialize(answer)


@router.put("/{answer_id}/accept")
def accept_answer(answer_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    question = db.query(Question).filter(Question.QuestionID == answer.QuestionID).first()

    is_question_owner = question.UserID == current_user["UserID"]
    is_mentor_or_admin = current_user.get("RoleID") in [ROLE_ADMIN, ROLE_MENTOR]

    # Normally only the question's author can accept an answer. The one
    # exception: an AI-generated answer needs a mentor/admin to review
    # and approve it before it's trusted enough to enter the Knowledge
    # Base - so mentors/admins can accept those even if they didn't ask
    # the question themselves.
    if not (is_question_owner or (is_mentor_or_admin and answer.IsAIGenerated)):
        raise HTTPException(
            status_code=403,
            detail="Only the question author can accept an answer (AI-generated answers can also be accepted by a mentor or admin).",
        )

    # Un-accept any previously accepted answer on this question
    for other in question.answers:
        if other.IsAccepted and other.AnswerID != answer_id:
            other.IsAccepted = False

    answer.IsAccepted = True
    question.StatusID = STATUS_ANSWERED

    answerer = db.query(User).filter(User.UserID == answer.UserID).first()
    if answerer and not answer.IsAIGenerated:
        gamify.award_points(db, answerer, gamify.POINTS_ACCEPTED_ANSWER, reason="Answer accepted")
        # "Top Mentor" is 5 accepted answers THIS MONTH, not lifetime -
        # consistent with every other badge now resetting monthly.
        accepted_count = db.query(Answer).filter(
            Answer.UserID == answerer.UserID,
            Answer.IsAccepted.is_(True),
            Answer.CreatedAt >= gamify.current_month_start(),
        ).count()
        if accepted_count >= 5:
            gamify.award_badge_manual(db, answerer, "Top Mentor")

        db.add(Notification(
            UserID=answerer.UserID,
            Type="answer_accepted",
            Message=f"Your answer to \"{question.Title}\" was accepted!",
            Link=f"/questions/{question.QuestionID}",
        ))

    db.commit()
    db.refresh(answer)

    return {"message": "Answer accepted successfully", "AnswerID": answer.AnswerID, "IsAccepted": answer.IsAccepted}


@router.put("/{answer_id}/upvote")
def upvote_answer(answer_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Toggles an upvote on/off for the current user on this answer.
    Was previously just `Upvotes += 1` on every call with no record of
    who'd already voted - meaning the same person clicking repeatedly
    (or just double-clicking) could inflate an answer's count and farm
    upvote points for its author without limit. Now backed by the Vote
    table: one vote per (user, answer), clicking again removes it."""
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    existing_vote = (
        db.query(Vote)
        .filter(Vote.AnswerID == answer_id, Vote.UserID == current_user["UserID"])
        .first()
    )

    author = db.query(User).filter(User.UserID == answer.UserID).first()

    if existing_vote:
        # Already upvoted - this click removes it.
        db.delete(existing_vote)
        answer.Upvotes = max(0, (answer.Upvotes or 0) - 1)
        if author:
            gamify.deduct_points(db, author, gamify.POINTS_UPVOTE_RECEIVED, reason="Upvote removed")
        upvoted = False
    else:
        db.add(Vote(AnswerID=answer_id, UserID=current_user["UserID"], VoteType=1))
        answer.Upvotes = (answer.Upvotes or 0) + 1
        if author:
            gamify.award_points(db, author, gamify.POINTS_UPVOTE_RECEIVED, reason="Received an upvote")
        upvoted = True

    db.commit()
    db.refresh(answer)

    return {"message": "Vote updated", "AnswerID": answer.AnswerID, "Upvotes": answer.Upvotes, "Upvoted": upvoted}


@router.put("/{answer_id}")
def update_answer(answer_id: int, payload: AnswerUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id, Answer.UserID == current_user["UserID"]).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    answer.AnswerText = payload.AnswerText
    if payload.AttachmentPath is not None:
        answer.AttachmentPath = payload.AttachmentPath
    db.commit()
    return {"message": "Answer updated successfully"}


@router.delete("/{answer_id}")
def delete_answer(answer_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    answer = db.query(Answer).filter(Answer.AnswerID == answer_id, Answer.UserID == current_user["UserID"]).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    author = db.query(User).filter(User.UserID == current_user["UserID"]).first()
    if author:
        gamify.deduct_points(db, author, gamify.POINTS_ANSWER_QUESTION, reason="Answer deleted")
        if answer.IsAccepted:
            gamify.deduct_points(db, author, gamify.POINTS_ACCEPTED_ANSWER, reason="Accepted answer deleted")

    db.delete(answer)
    db.commit()
    return {"message": "Answer deleted successfully"}
