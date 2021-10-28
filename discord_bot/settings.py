FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

bot_token = ''
telegram_token = ''
chat_id = ''
yt_username = ''
yt_password = ''
yt_cookie_path = ''

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
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'username': yt_username,
    'password': yt_password,
    'cookiefile': yt_cookie_path
}

telegram_nick = {
    '<@!291599775936282624>': '@agarbuzov ',
    '<@!299154812858269697>': '@Tema_N7',
    '<@!289480655551856641>': '@Gelbart',
    '<@!170224964429938689>': '@w4ri0ck',
}
