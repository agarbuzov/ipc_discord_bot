from fastapi import FastAPI

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

from front.routes import router
from front.exceptions import Forbidden
from front.middleware import set_user
from front.handlers import forbidden_handler

app = FastAPI()
app.mount("/static", StaticFiles(directory="front/static"), name="static")
app.add_middleware(BaseHTTPMiddleware, dispatch=set_user)
app.add_exception_handler(Forbidden, forbidden_handler)
app.include_router(router)
