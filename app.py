import settings

from flask import Flask
from front.base.routes import base
from front.player.routes import player
from front.alerts.routes import alerts
from front.base.middleware import user_middleware
from front.base.middleware import bot_middleware
from front.base.handlers import error_handler
from werkzeug.exceptions import HTTPException

app = Flask(__name__, static_folder="front/static", template_folder=None)
app.config.from_object(settings)
app.register_blueprint(base)
app.register_blueprint(player)
app.register_blueprint(alerts)
app.before_request(user_middleware)
app.before_request(bot_middleware)
app.register_error_handler(HTTPException, error_handler)

if __name__ == "__main__":
    app.run(host="localhost", port=8000, debug=settings.DEBUG)
