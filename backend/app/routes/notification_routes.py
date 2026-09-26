from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Notification
from app.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize(n: Notification):
    return {
        "NotificationID": n.NotificationID,
        "Type": n.Type,
        "Message": n.Message,
        "Link": n.Link,
        "IsRead": n.IsRead,
        "CreatedAt": n.CreatedAt,
    }


@router.get("/")
def get_my_notifications(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = (
        db.query(Notification)
        .filter(Notification.UserID == current_user["UserID"])
        .order_by(Notification.CreatedAt.desc())
        .limit(50)
        .all()
    )
    return [_serialize(n) for n in notifications]


@router.get("/unread-count")
def unread_count(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    count = (
        db.query(Notification)
        .filter(Notification.UserID == current_user["UserID"], Notification.IsRead.is_(False))
        .count()
    )
    return {"UnreadCount": count}


@router.put("/{notification_id}/read")
def mark_read(notification_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    notification = (
        db.query(Notification)
        .filter(Notification.NotificationID == notification_id, Notification.UserID == current_user["UserID"])
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.IsRead = True
    db.commit()
    return {"message": "Notification marked as read"}


@router.put("/read-all")
def mark_all_read(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.UserID == current_user["UserID"], Notification.IsRead.is_(False)
    ).update({Notification.IsRead: True})
    db.commit()
    return {"message": "All notifications marked as read"}
