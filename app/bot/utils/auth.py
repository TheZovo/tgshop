from db.session import SessionLocal
from db.models.user import User

def is_admin(telegram_id: str) -> bool:
    with SessionLocal() as session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        return user.is_admin if user else False