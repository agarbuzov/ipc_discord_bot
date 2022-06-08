import requests
import settings

from models import session
from models import User
from models import UserSession

from PIL import Image
from io import BytesIO


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
        "redirect_uri": settings.REDIRECT_URL
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


async def get_user_guilds(token_type, token):
    url = "https://discord.com/api/v10/users/@me/guilds"
    headers = {"Authorization": f"{token_type} {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


async def get_user_icon(user_id):
    avatar = session.query(User).get(user_id).avatar
    url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png?size=128"
    return url


def get_dominated_colors(image_url, numcolors=3, resize=150):
    response = requests.get(image_url)

    img = Image.open(BytesIO(response.content))
    img = img.copy()
    img.thumbnail((resize, resize))

    paletted = img.convert('P', palette=Image.ADAPTIVE, colors=numcolors)
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)
    colors = list()

    for i in range(numcolors):
        palette_index = color_counts[i][1]
        dominant_color = palette[palette_index*3:palette_index*3+3]
        colors.append(tuple(dominant_color))

    return {'colors': colors}


def add_colors(guild: dict):
    color = get_dominated_colors(guild['icon'])
    guild.update(color)
