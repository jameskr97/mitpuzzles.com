from typing import Union

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

from accounts.models import User
from tracking.models import Visitor


def get_current_actor(scope) -> Union[User, Visitor, None]:
    """
    Returns the current actor for a websocket or HTTP request:
    - If authenticated, returns the User
    - Else, returns the Visitor based on the 'visitor_id' cookie
    - Returns None if neither exists
    """
    user = scope.get("user")
    cookies = scope.get("cookies", {})
    visitor_id = cookies.get("visitor_id")

    if user and user.is_authenticated:
        return user

    if visitor_id:
        try:
            return Visitor.objects.get(id=visitor_id)
        except Visitor.DoesNotExist:
            return None

    return None

async def aget_current_actor(scope) -> Union[User, Visitor, None]:
    """
    Returns the current actor for a websocket or HTTP request:
    - If authenticated, returns the User
    - Else, returns the Visitor based on the 'visitor_id' cookie
    - Returns None if neither exists
    """
    user = scope.get("user")
    cookies = scope.get("cookies", {})
    visitor_id = cookies.get("visitor_id")

    if user and user.is_authenticated:
        return user

    if visitor_id:
        try:
            return await database_sync_to_async(Visitor.objects.get)(id=visitor_id)
        except Visitor.DoesNotExist:
            return None

    return None
