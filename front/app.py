from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})


@app.get("/history/", response_class=HTMLResponse)
async def history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/playlists/", response_class=HTMLResponse)
async def playlists(request: Request):
    return templates.TemplateResponse("playlists.html", {"request": request})


@app.get("/playlists/create/", response_class=HTMLResponse)
async def playlist_create(request: Request):
    return templates.TemplateResponse("playlist_create.html", {"request": request})
