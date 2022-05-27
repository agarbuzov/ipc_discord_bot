FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Discord bot token
BOT_TOKEN = ""

# Telegram bot credentials
TELEGRAM_TOKEN = ""
CHAT_ID = ""

# Google account credentials for youtube
YT_USERNAME = ""
YT_PASSWORD = ""
YT_COOKIE_PATH = ""
YT_API_KEY = ""

# Discord app tokens for front app
CLIENT_ID = ""
SECRET = ""

# Url for discord oauth redirect
REDIRECT_URL = ""

try:
    from local_settings import *
except:
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
    'source_address': '0.0.0.0',
    'username': YT_USERNAME,
    'password': YT_PASSWORD,
    'cookiefile': YT_COOKIE_PATH
}

TELEGRAM_NICK = {
    '291599775936282624': '@agarbuzov ',
    '299154812858269697': '@Tema_N7',
    '289480655551856641': '@Gelbart',
    '170224964429938689': '@w4ri0ck',
}
