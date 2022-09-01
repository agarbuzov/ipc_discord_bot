from flask import Blueprint

from front.alerts.views import AlertsIndex
from front.alerts.views import AlertsCreate
from front.alerts.views import AlertsDelete

alerts = Blueprint("alerts", __name__, url_prefix="/alerts/", template_folder="templates/")

alerts.add_url_rule("/", view_func=AlertsIndex.as_view("index"))
alerts.add_url_rule("/create/", view_func=AlertsCreate.as_view("create"))
alerts.add_url_rule("/delete/", view_func=AlertsDelete.as_view("delete"))
