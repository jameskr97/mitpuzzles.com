from fastapi import Depends

from app.modules.authentication import User, fastapi_users


async def require_admin(user: User = Depends(fastapi_users.current_user(active=True, superuser=True))):
    return user
