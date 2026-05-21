from sqlalchemy.orm import Session
from ..models import User, Thread, Message, Response
from datetime import datetime, timedelta


def get_user_stats(db: Session, user_id: int):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return None
    
    thread_count = db.query(Thread).filter_by(user_id=user_id).count()
    message_count = db.query(Message).join(Thread).filter(Thread.user_id == user_id).count()
    
    return {
        "user_id": user_id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "threads": thread_count,
        "messages": message_count,
        "created_at": user.created_at
    }


def get_thread_messages(db: Session, thread_id: int, limit: int = 100):
    messages = db.query(Message).filter_by(thread_id=thread_id).order_by(Message.created_at.desc()).limit(limit).all()
    return list(reversed(messages))


def delete_old_messages(db: Session, days: int = 90):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(Message).filter(Message.created_at < cutoff_date).delete()
    db.commit()
    return deleted


def get_recent_messages(db: Session, hours: int = 24, limit: int = 50):
    cutoff_date = datetime.utcnow() - timedelta(hours=hours)
    messages = db.query(Message).filter(Message.created_at >= cutoff_date).order_by(Message.created_at.desc()).limit(limit).all()
    return list(reversed(messages))
