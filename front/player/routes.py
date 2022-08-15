from flask import Blueprint

from front.player.views import PlayerSearch
from front.player.views import PlayerPlaylist
from front.player.views import PlayerPlaylists

player = Blueprint("player", __name__, url_prefix="/player/", template_folder="templates/")

player.add_url_rule("/search/", view_func=PlayerSearch.as_view("search"))
player.add_url_rule("/playlists/", view_func=PlayerPlaylists.as_view("playlists"))
player.add_url_rule("/playlists/<int:playlist_id>/", view_func=PlayerPlaylist.as_view("playlist"))
