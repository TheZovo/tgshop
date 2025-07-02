from db.session import SessionLocal
from db.models.user import User

async def check_user_not_banned(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        return user and not user.is_banned