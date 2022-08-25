import asyncio
import settings

from datetime import timedelta
from typing import Optional
from async_timeout import timeout

from discord import Member
from discord import TextChannel
from discord import VoiceChannel
from discord import FFmpegPCMAudio
from discord.ext.commands import Cog
from discord.ext.commands import command

from youtube_dl import YoutubeDL

yt_dl = YoutubeDL(settings.YTDL_OPTIONS)


class Music(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.current_player = None
        self.players = {}

    async def cog_before_invoke(self, ctx):
        self.current_player: Player = self.players.get(ctx.guild.id)

    async def create_player(self, channel: TextChannel, author: Member):
        self.players[channel.guild.id] = await Player(self, self.bot, channel, author.voice.channel).create()

    async def add_to_queue(self, query):
        track = await Track(query).fetch()
        await self.current_player.queue.put(track)

    async def cleanup(self, guild):
        del self.players[guild.id]

    @command(name="play")
    async def _play(self, ctx, *, query):
        channel = ctx.channel
        author = ctx.author

        await self.create_player(channel, author)
        self.current_player = self.players[channel.guild.id]
        await self.add_to_queue(query)


class Player:

    def __init__(self, cog: Music, bot, channel: TextChannel, voice: VoiceChannel):
        self.queue = PlayQueue()
        self.event = asyncio.Event()
        self.cog = cog
        self.bot = bot
        self.channel = channel
        self.voice = voice
        self.voice_state = None
        self.current = None
        self.loop_task = self.bot.loop.create_task(self.player_loop())

    def __del__(self):
        self.loop_task.cancel()

    async def create(self):
        await self.connect()
        return self

    async def connect(self):
        async with self.channel.typing():
            self.voice_state = await self.voice.connect()

    async def player_loop(self):
        while True:
            self.event.clear()

            try:
                async with timeout(10):
                    self.current = await self.queue.get()
            except asyncio.TimeoutError:
                return await self.destroy()

            self.voice_state.play(self.current, after=self.next)
            await self.current.create_source()
            await self.event.wait()

    async def next(self, error=None):
        self.event.set()

    async def destroy(self):
        await self.voice_state.disconnect()
        return await self.cog.cleanup(self.voice.guild)


class Track:

    def __init__(self, query) -> None:
        self._query: str = query
        self._duration: Optional[int] = None
        self.url: Optional[str] = None
        self.title: Optional[str] = None

    async def fetch(self):
        data = yt_dl.extract_info(self._query, download=False)
        data = data.get("entries", [{}])[0]
        self._duration = data.get("duration")
        self.title = data.get("title")
        self.url = data.get("webpage_url")
        return self

    async def create_source(self) -> FFmpegPCMAudio:
        data = yt_dl.extract_info(self.url, download=False)
        url = data.get("url")
        return FFmpegPCMAudio(url, **settings.FFMPEG_OPTIONS)

    @property
    def duration(self) -> Optional[str]:
        return str(timedelta(seconds=self._duration))


class PlayQueue(asyncio.Queue):

    async def get(self) -> Track:
        return await super().get()
