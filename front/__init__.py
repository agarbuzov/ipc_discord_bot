import settings
import youtube_dl

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="front/templates")

settings.YTDL_OPTIONS['skip_download'] = True
settings.YTDL_OPTIONS['extract_flat'] = True
ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)
