from typing import Optional
from models import session
from models import Notification

from discord import Embed
from discord import Color
from discord.ext.commands import Bot
from discord.ext.commands import Cog

from front.notifications.utils import twitch_api_request


class Notifications(Cog):

    def __init__(self, bot):
        self.bot: Optional[Bot] = bot
        self.stream_data: Optional[dict] = None
        self.user_data: Optional[dict] = None
        self.category_data: Optional[dict] = None
        self.embed: Optional[Embed] = None

    async def get_stream_data(self, broadcaster_id):
        params = {"user_id": broadcaster_id}
        response = twitch_api_request("get", "/streams/", params=params)
        self.stream_data = response.get("data")[0]

    async def get_user_data(self, broadcaster_id):
        params = {"id": broadcaster_id}
        response = twitch_api_request("get", "/users/", params=params)
        self.user_data = response.get("data")[0]

    async def get_category_data(self):
        params = {"id": self.stream_data.get("game_id")}
        response = twitch_api_request("get", "/games/", params=params)
        self.category_data = response.get("data")[0]

    async def create_embed(self):
        self.embed = Embed(
            title=self.stream_data.get("title"),
            url=f"https://twitch.tv/{self.stream_data.get('user_name')}",
            colour=Color.red()
        )
        self.embed.set_thumbnail(url=self.category_data.get("box_art_url").format(width=250, height=330))
        self.embed.set_image(url=self.stream_data.get("thumbnail_url").format(width=400, height=225))
        self.embed.set_author(name=self.stream_data.get("user_name"),
                              icon_url=self.user_data.get("profile_image_url"))
        self.embed.add_field(name="Категория", value=self.stream_data.get("game_name"))
        self.embed.add_field(name="Зрителей", value=self.stream_data.get("viewer_count"))

    async def send(self, broadcaster_id):
        await self.get_stream_data(broadcaster_id)
        await self.get_user_data(broadcaster_id)
        await self.get_category_data()
        await self.create_embed()
        targets = session.query(Notification).filter(Notification.broadcaster_id == broadcaster_id).all()
        for target in targets:
            guild = self.bot.get_guild(target.guild_id)
            channel = guild.get_channel(target.channel_id)
            await channel.send(target.body, embed=self.embed)
