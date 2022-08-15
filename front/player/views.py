from flask import request
from flask import render_template
from flask.views import MethodView

from models import Playlist
from models import session as db_session

from front.base.decorators import token_required

from youtubesearchpython import VideosSearch


class PlayerSearch(MethodView):

    @staticmethod
    @token_required
    def get():
        return render_template("player/search.html")

    @staticmethod
    @token_required
    def post():
        query = request.form.get("query")
        result = VideosSearch(query, limit=50).result()["result"]
        return render_template("player/search.html", result=result)


class PlayerPlaylists(MethodView):

    @staticmethod
    @token_required
    def get():
        playlists = db_session.query(Playlist).all()
        return render_template("player/playlists.html", playlists=playlists)


class PlayerPlaylist(MethodView):

    @staticmethod
    @token_required
    def get(playlist_id):
        playlist = db_session.query(Playlist).get(playlist_id)
        return render_template("player/playlist.html", playlist=playlist)
