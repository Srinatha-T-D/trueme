from sqlalchemy import select
from app.models.user import User

async def get_user_role(db, user_id: int) -> str:
    user = await db.get(User, user_id)
    return user.role
