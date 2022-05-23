import requests
import settings

from models import session
from models import User
from models import UserSession


async def get_current_user(token: str):
    user = session.query(UserSession).get(token)
    return user


async def get_token(code):
    url = "https://discord.com/api/oauth2/token"
    data = {
        "code": code,
        "client_id": settings.CLIENT_ID,
        "client_secret": settings.SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:8000/auth/"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=data, headers=headers)
    return response.json()


async def get_user(token_type, token):
    url = "https://discord.com/api/v10/users/@me"
    headers = {"Authorization": f"{token_type} {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


async def get_user_icon(user_id):
    avatar = session.query(User).get(user_id).avatar
    url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png?size=64"
    return url
