import requests
import settings


def generate_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": settings.TWITCH_CLIENT_ID,
        "client_secret": settings.CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        return token


def validate_token(token):
    url = "https://id.twitch.tv/oauth2/validate"
    headers = {"Authorization": f"OAuth {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
