from typing import Optional

import requests
from discord import Color
from discord import Embed
from discord.ext.commands import Bot
from discord.ext.commands import Cog

from front.base.utils import twitch_api_request
from models import Alert
from models import session
from settings import IMGUR_CLIENT_ID


class Alerts(Cog):

    def __init__(self, bot) -> None:
        self.bot: Optional[Bot] = bot
        self.stream_data: Optional[dict] = None
        self.user_data: Optional[dict] = None
        self.category_data: Optional[dict] = None
        self.embed: Optional[Embed] = None
        self.image: Optional[str] = None

    async def get_stream_data(self, broadcaster_id) -> None:
        params = {"user_id": broadcaster_id}
        response = twitch_api_request("get", "/streams/", params=params)
        self.stream_data = data[0] if (data := response.get("data")) else {}

    async def get_user_data(self, broadcaster_id) -> None:
        params = {"id": broadcaster_id}
        response = twitch_api_request("get", "/users/", params=params)
        self.user_data = data[0] if (data := response.get("data")) else {}

    async def get_category_data(self) -> None:
        params = {"id": self.stream_data.get("game_id")}
        response = twitch_api_request("get", "/games/", params=params)
        self.category_data = data[0] if (data := response.get("data")) else ""

    async def upload_image(self) -> None:
        """
        Upload image on imgur, because twitch link unavailable when stream is ends
        If imgur link unavailable use twitch link
        """
        twitch_link = self.stream_data.get("thumbnail_url").format(width=400, height=225)
        response = requests.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
            params={"image": twitch_link}
        )
        imgur_link = response.json().get("data", {}).get("link") if response.ok else None
        self.image = imgur_link if imgur_link else twitch_link

    async def create_embed(self) -> None:
        self.embed = Embed(
            title=self.stream_data.get("title"),
            url=f"https://twitch.tv/{self.stream_data.get('user_name')}",
            colour=Color.red()
        )
        self.embed.set_thumbnail(url=self.category_data.get("box_art_url").format(width=250, height=330))
        self.embed.set_image(url=self.image)
        self.embed.set_author(name=self.stream_data.get("user_name"),
                              icon_url=self.user_data.get("profile_image_url"))
        self.embed.add_field(name="Категория", value=self.stream_data.get("game_name"))
        self.embed.add_field(name="Зрителей", value=self.stream_data.get("viewer_count"))

    async def send(self, broadcaster_id) -> None:
        await self.get_stream_data(broadcaster_id)
        await self.get_user_data(broadcaster_id)
        await self.get_category_data()
        await self.upload_image()
        await self.create_embed()
        targets = session.query(Alert).filter_by(broadcaster_id=broadcaster_id).all()
        for target in targets:
            guild = self.bot.get_guild(target.guild_id)
            channel = guild.get_channel(target.channel_id)
            await channel.send(target.body, embed=self.embed)
