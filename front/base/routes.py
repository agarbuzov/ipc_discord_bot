from flask import Blueprint

from front.base.views import Index
from front.base.views import Login
from front.base.views import Auth
from front.base.views import Logout
from front.base.views import Profile
from front.base.views import Test

base = Blueprint("", __name__, template_folder="templates/")

base.add_url_rule("/", view_func=Index.as_view("index"))
base.add_url_rule("/login/", view_func=Login.as_view("login"))
base.add_url_rule("/auth/", view_func=Auth.as_view("auth"))
base.add_url_rule("/logout/", view_func=Logout.as_view("logout"))
base.add_url_rule("/profile/", view_func=Profile.as_view("profile"))

base.add_url_rule("/test/", view_func=Test.as_view("test"))
