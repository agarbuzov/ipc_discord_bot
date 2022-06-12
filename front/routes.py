import json
import base64
import asyncio
import datetime
import functools
import websockets

from fastapi import File
from fastapi import Form
from fastapi import Request
from fastapi import Depends
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from models import session
from models import User
from models import Track
from models import Guild
from models import History
from models import Playlist
from models import UserSession

from front import ytdl
from front import templates
from front.utils import get_token
from front.utils import get_user
from front.utils import get_user_guilds
from front.utils import add_colors
from front.dependecies import is_authorized
from front.exceptions import WebsocketUnavailable

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("base.html", {"request": request})


@router.get("/history/", response_class=HTMLResponse)
async def history(request: Request, authorize=Depends(is_authorized)):
    history_ = session.query(History).order_by(History.date.desc()).limit(50).all()
    return templates.TemplateResponse("history.html", {"request": request, "history": history_})


@router.get("/playlists/", response_class=HTMLResponse)
async def playlists(request: Request, authorize=Depends(is_authorized)):
    playlists_ = session.query(Playlist).order_by(Playlist.id.desc()).all()
    return templates.TemplateResponse("playlists.html", {"request": request, "playlists": playlists_})


@router.get("/playlists/create/", response_class=HTMLResponse)
async def playlist_create(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("playlist_create.html", {"request": request})


@router.post("/playlists/create/")
async def playlist_create_post(request: Request, authorize=Depends(is_authorized), name: str = Form(),
                               tracks: list = Form(), cover: UploadFile = File()):
    tracks = json.loads(tracks[0])
    author = request.state.session.user.id
    b64_cover = base64.b64encode(await cover.read())
    playlist = Playlist(name=name, creator_id=author, tracks=[Track(
        url=track.get("url"),
        name=track.get("title"),
        duration=track.get("duration")
    ) for track in tracks if track.get('url')], cover=b64_cover.decode('utf-8'), cover_type=cover.content_type)
    session.add(playlist)
    session.commit()
    return "/playlists"


@router.get("/auth/")
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
            user = User(
                **{k: v for k, v in user_data.items() if k in [column.name for column in User.__table__.columns]})

    for guild in user_guilds:

        if guild_ := session.query(Guild).get(guild.get('id')):
            if guild_ not in user.guilds:
                user.guilds.append(guild_)
        else:
            guild = Guild(id=guild.get('id'), name=guild.get('name'))
            user.guilds.append(guild)

    session.add(user)
    session.commit()
    response = RedirectResponse('/')
    response.set_cookie('session', token)
    return response


@router.get("/search/")
async def search(count: int, query: str, authorize=Depends(is_authorized)):
    partial = functools.partial(ytdl.extract_info, f'ytsearch{count}:{query}', download=False)
    data = await asyncio.get_event_loop().run_in_executor(None, partial)
    if data:
        result = [
            {
                "url": f"https://www.youtube.com/watch?v={track.get('id')}",
                "title": track.get("title") if len(track.get("title")) < 50 else track.get("title")[:50] + "...",
                "duration": str(datetime.timedelta(seconds=track['duration']))
            }
            for track in data.get("entries") if track.get("duration")
        ]
        return result


@router.get("/play/")
async def play(query: str, request: Request, authorize=Depends(is_authorized)):
    async with websockets.connect("ws://localhost:5001") as websocket:
        await websocket.send(json.dumps({"e": "play", "d": {"user": request.state.session.user.id, "query": query}}))
        response = json.loads(await websocket.recv())
        return response


@router.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/guilds/", response_class=HTMLResponse)
async def get_guilds(request: Request, authorize=Depends(is_authorized)):
    try:
        async with websockets.connect("ws://localhost:5001") as websocket:
            await websocket.send(json.dumps({"e": "get_guilds"}))
            guilds = json.loads(await websocket.recv())
    except ConnectionRefusedError:
        raise WebsocketUnavailable

    loop = asyncio.get_event_loop()
    futures = [loop.run_in_executor(None, add_colors, guild) for guild in guilds if guild['icon']]
    await asyncio.gather(*futures)

    return templates.TemplateResponse("guilds.html", {"request": request, 'guilds': guilds})


@router.get("/settings/", response_class=HTMLResponse)
async def bot_settings(request: Request, authorize=Depends(is_authorized)):
    return templates.TemplateResponse("settings.html", {"request": request})
