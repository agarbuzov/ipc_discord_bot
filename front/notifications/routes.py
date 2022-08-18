from flask import Blueprint

from front.notifications.views import NotificationsIndex
from front.notifications.views import NotificationsDelete
from front.notifications.views import NotificationsCreate
from front.notifications.views import NotificationsReceive

notifications = Blueprint("notifications", __name__, url_prefix="/notifications/", template_folder="templates/")

notifications.add_url_rule("/", view_func=NotificationsIndex.as_view("index"))
notifications.add_url_rule("/create/", view_func=NotificationsCreate.as_view("create"))
notifications.add_url_rule("/delete/", view_func=NotificationsDelete.as_view("delete"))
notifications.add_url_rule("/<string:platform>/", view_func=NotificationsReceive.as_view("receive"))
