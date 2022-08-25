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

# YTDL settings
YT_COOKIE_PATH = None

DEBUG = False

try:
    from local_settings import *
except ImportError:
    pass

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'cachedir': False,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
