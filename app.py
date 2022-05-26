import requests
import settings

from fastapi import FastAPI
from fastapi import Request

from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from front.utils import get_token
from front.utils import get_user
from front.utils import get_current_user
from front.utils import get_user_icon

from models import session
from models import User
from models import UserSession
from models import History

app = FastAPI()

app.mount("/static", StaticFiles(directory="front/static"), name="static")

templates = Jinja2Templates(directory="front/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/history/", response_class=HTMLResponse)
async def history(request: Request):
    history_ = session.query(History).order_by(History.date.desc()).limit(50).all()
    return templates.TemplateResponse("history.html", {"request": request, "history": history_})


@app.get("/playlists/", response_class=HTMLResponse)
async def playlists(request: Request):
    return templates.TemplateResponse("playlists.html", {"request": request})


@app.get("/playlists/create/", response_class=HTMLResponse)
async def playlist_create(request: Request):
    return templates.TemplateResponse("playlist_create.html", {"request": request})


@app.get("/auth/")
async def auth(code: str):
    authorization_data = await get_token(code)
    token_type = authorization_data.get('token_type')
    token = authorization_data.get('access_token')
    user_data = await get_user(token_type, token)
    user = session.query(User).get(user_data.get('id'))
    user_session = session.query(UserSession).get(token)
    if not user_session:
        user_session = UserSession(user_id=user_data.get('id'), session=token)
        session.add(user_session)
    if not user:
        user = User(**{k: v for k, v in user_data.items() if k in [column.name for column in User.__table__.columns]})
        session.add(user)
    session.commit()
    response = RedirectResponse('/')
    response.set_cookie('session', token)
    return response


@app.get("/search/")
async def search(query: str):
    url = "https://youtube.googleapis.com/youtube/v3/search"
    params = {
        "key": settings.YT_API_KEY,
        "q": query,
        "maxResult": 5,
        "part": "snippet",
        "type": "video"
    }
    response = requests.get(url=url, params=params)
    data = response.json()
    print(data['items'][0]['id']['videoId'])
    result = [{'id': result['id']['videoId'], 'icon': result['snippet']['thumbnails']['default']['url'],
               'title': result['snippet']['title']} for result in data['items']]
    return result


# @app.get('/guilds/')
# async def guilds():
#     async with websockets.connect("ws://localhost:8765") as websocket:
#         await websocket.send(json.dumps({"event": "get_guilds"}))
#         result = dill.loads(await websocket.recv())
#     return result


@app.middleware("http")
async def set_user(request: Request, call_next):
    if token := request.cookies.get('session'):
        user_session = await get_current_user(token)
        request.state.session = user_session
        if user_session.user.avatar:
            request.state.user_icon = await get_user_icon(user_session.user.id)
    response = await call_next(request)
    return response
