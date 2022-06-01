import settings

from fastapi import Request
from fastapi import HTTPException
from fastapi import status

from front.exceptions import Forbidden


async def is_authorized(request: Request):
    if not hasattr(request.state, "session"):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login/"})
    if settings.PERMITTED_GUILD not in request.state.session.user.get_guilds():
        raise Forbidden
