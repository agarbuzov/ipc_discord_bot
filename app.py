import json
import asyncio
import settings
import functools
import youtube_dl
import websockets
import urllib.parse

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi import Depends
from fastapi import HTTPException

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from front.utils import get_token
from front.utils import get_user
from front.utils import get_current_user
from front.utils import get_user_icon
from front.utils import get_user_guilds

from models import session
from models import User
from models import UserSession
from models import History
from models import Playlist
from models import Guild

app = FastAPI()

app.mount("/static", StaticFiles(directory="front/static"), name="static")

templates = Jinja2Templates(directory="front/templates")

settings.YTDL_OPTIONS['skip_download'] = True
settings.YTDL_OPTIONS['extract_flat'] = True
ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)


async def is_authorized(request: Request):
    if not hasattr(request.state, 'session'):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={'Location': '/login/'})
    if settings.PERMITTED_GUILD not in request.state.session.user.get_guilds():
        raise Forbidden


class Forbidden(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN)


@app.exception_handler(Forbidden)
async def forbidden(request):
    return templates.TemplateResponse("error403.html", {"request": request}, status_code=403)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/history/", response_class=HTMLResponse)
async def history(request: Request, authorize=Depends(is_authorized)):
    history_ = session.query(History).order_by(History.date.desc()).limit(50).all()
    return templates.TemplateResponse("history.html", {"request": request, "history": history_})


@app.get("/playlists/", response_class=HTMLResponse)
async def playlists(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("playlists.html", {"request": request})


@app.get("/playlists/create/", response_class=HTMLResponse)
async def playlist_create(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("playlist_create.html", {"request": request})


@app.get("/auth/")
async def auth(code: str):
    authorization_data = await get_token(code)
    token_type = authorization_data.get('token_type')
    token = authorization_data.get('access_token')

    user_data = await get_user(token_type, token)
    user_guilds = await get_user_guilds(token_type, token)
    user = session.query(User).get(user_data.get('id'))
    user_session = session.query(UserSession).get(token)

    if user_data:

        if not user_session:
            user_session = UserSession(user_id=user_data.get('id'), session=token)
            session.add(user_session)

        if not user:
            user = User(**{k: v for k, v in user_data.items() if k in [column.name for column in User.__table__.columns]})

    for guild in user_guilds:

        if guild := session.query(Guild).get(guild.get('id')):
            if guild not in user.guilds:
                user.guilds.append(guild)
        else:
            guild = Guild(id=guild.get('id'), name=guild.get('name'))
            user.guilds.append(guild)

    session.add(user)
    session.commit()
    response = RedirectResponse('/')
    response.set_cookie('session', token)
    return response


@app.get("/search/")
async def search(query: str, authorize=Depends(is_authorized)):
    partial = functools.partial(ytdl.extract_info, f'ytsearch5:{query}', download=False)
    data = await asyncio.get_event_loop().run_in_executor(None, partial)
    result = [
        {
            'url': f'https://www.youtube.com/watch?v={track.get("id")}',
            'title': track.get('title') if len(track.get('title')) < 50 else track.get('title')[:50] + '...'
        }
        for track in data.get('entries')
    ]
    return result


@app.get("/play/")
async def play(query: str, request: Request, authorize=Depends(is_authorized)):
    async with websockets.connect("ws://localhost:5001") as websocket:
        await websocket.send(json.dumps({"e": "play", "d": {"user": request.state.session.user.id, "query": query}}))
        response = json.loads(await websocket.recv())
        return response


@app.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# @app.get('/guilds/')
# async def guilds():
#     async with websockets.connect("ws://localhost:8765") as websocket:
#         await websocket.send(json.dumps({"event": "get_guilds"}))
#         result = dill.loads(await websocket.recv())
#     return result


@app.middleware("http")
async def set_user(request: Request, call_next):
    if user_session := await get_current_user(request.cookies.get('session')):
        request.state.session = user_session
        if user_session.user.avatar:
            request.state.user_icon = await get_user_icon(user_session.user.id)
    request.state.redirect_url = urllib.parse.quote(settings.REDIRECT_URL, safe='')
    response = await call_next(request)
    return response
