import settings
import urllib.parse

from fastapi import Request

from front.utils import get_current_user
from front.utils import get_user_icon


async def set_user(request: Request, call_next):
    if user_session := await get_current_user(request.cookies.get("session")):
        request.state.session = user_session
        if user_session.user.avatar:
            request.state.user_icon = await get_user_icon(user_session.user.id)
    request.state.redirect_url = urllib.parse.quote(settings.REDIRECT_URL, safe="")
    response = await call_next(request)
    return response
