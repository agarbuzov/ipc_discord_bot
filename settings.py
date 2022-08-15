# Discord bot credentials
BOT_TOKEN = None

# Twitch credentials
TWITCH_CLIENT_ID = None
TWITCH_CLIENT_SECRET = None

# Discord app credential
DISCORD_CLIENT_ID = None
DISCORD_SECRET = None

# Trovo credentials
TROVO_CLIENT_ID = None
TROVO_SECRET = None

# Flask settings
SECRET_KEY = None

DEBUG = False

try:
    from local_settings import *
except:
    pass
