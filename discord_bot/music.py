import asyncio
import json
import functools
import inflect

from datetime import datetime
from async_timeout import timeout

import discord
from discord.ext import commands
from utils import emoji
import youtube_dl

import settings


def validation(func):

    async def wrapper(self, ctx):

        if not self.voice_client:
            return await ctx.send(f'{emoji.failure} **Bot is not connected to any voice channel on guild**')

        return await func(self, ctx)
    return wrapper


class MusicPlayer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)
        self.players = dict()
        self.player = None
        self.voice_client = None

    async def cog_before_invoke(self, ctx: commands.Context):

        self.player = self.players.get(ctx.guild.id)

        self.voice_client = ctx.guild.voice_client

    @commands.command(name="play")
    async def _play(self, ctx: commands.Context, *, query: str):
        """
        Play youtube track
        """
        with ctx.typing():

            if not query:
                return await ctx.channel.send(f'{emoji.failure} **No data passed**')

            if not self.voice_client:
                # if not connected to some guild channel -> connect to author voice channel
                author_voice_state = ctx.author.voice

                if not author_voice_state:
                    # if user not connected to some voice channel
                    return await ctx.channel.send(f'{emoji.failure} '
                                                  f'**You are not connected to any voice channel on guild**')

                self.voice_client = await author_voice_state.channel.connect()

            elif self.voice_client and self.voice_client.channel.id != ctx.author.voice.channel.id:
                # if user in another voice channel -> move to him voice channel
                await self.voice_client.move_to(ctx.author.voice.channel)

            result = await self.search(query)

            await self.send_embed(ctx, query, result['title'], self.voice_client)

            if not self.player:
                self.player = Player(ctx, self.bot)
                self.players[ctx.guild.id] = self.player

            self.player.voice = self.voice_client
            track = Track(result['url'], result['title'])
            await self.player.queue.put(track)

    @commands.command(name="pause", aliases=['p'])
    @validation
    async def _pause(self, ctx: commands.Context):
        """
        Pause current track
        """
        if self.voice_client.is_paused():
            return await ctx.send(f'{emoji.failure} **Already paused**')

        self.voice_client.pause()
        await ctx.send(f'{emoji.pause_button} **Paused**')

    @commands.command(name="resume", aliases=['r'])
    @validation
    async def _resume(self, ctx: commands.Context):
        """
        Resume current track
        """
        if self.voice_client.is_playing():
            return await ctx.send(f'{emoji.failure} **Already playing**')

        self.voice_client.resume()
        await ctx.send(f'{emoji.pause_button} **Resumed**')

    @commands.command(name="stop", aliases=['s'])
    @validation
    async def _stop(self, ctx: commands.Context):
        """
        Clear queue and stop playing
        """
        if self.player.queue > 0:
            self.player.queue.clear()

        self.player.voice.stop()
        await ctx.send(f'{emoji.stop_button} **Stopped**')

    @commands.command(name='queue', aliases=['q', 'que'])
    async def _queue(self, ctx: commands.Context):
        """
        Get list of track in queue
        """
        player = self.players.get(ctx.guild.id)
        corrector = inflect.engine()
        queue = ''

        for i, track in enumerate(player.queue):
            queue += f'{i+1}.{track.title}\n'

        embed = discord.Embed(title=f'{emoji.notes} {len(player.queue)}'
                                    f' {corrector.plural("track", len(player.queue))} in queue',
                              description=f'{queue}')
        await ctx.send(embed=embed)

    @commands.command(name="next", aliases=['skip', 'nx', 'sk'])
    @validation
    async def _next(self, ctx: commands.Context):
        """
        Skip current track in queue
        """
        if not (self.player.voice.is_paused() or self.player.voice.is_playing()):
            return await ctx.send(f'{emoji.failure} **Nothing to skip**')

        self.player.loop = False

        self.player.voice.stop()
        await ctx.send(f'{emoji.next_track} **Skipped**')
        if self.player.voice.is_playing() and self.player.current:
            await ctx.send(f'{emoji.youtube_icon} **Playing** `{self.player.current.title}`')

    @commands.command(name="now")
    async def _now(self, ctx: commands.Context):
        """
        Get current track
        """
        if not self.player.voice.is_playing():
            return await ctx.send(f'{emoji.failure} **Nothing is playing now**')

        await ctx.send(f'{emoji.play_pause} `{self.player.current.title}` **is playing now**')

    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int):
        """
        Remove track from queue by index
        """
        if self.player.queue == 0:
            return await ctx.send(f'{emoji.failure} **Queue is empty**')

        self.player.queue.remove(index - 1)
        await ctx.send(f'{emoji.success} `{self.player.queue[index - 1].title}` **removed from queue**')

    @commands.command(name='clear', aliases=['cl'])
    async def _clear(self, ctx: commands.Context):
        """
        Clear the queue
        """
        if len(self.player.queue) == 0:
            return await ctx.send(f'{emoji.failure} **Queue is empty**')

        self.player.queue.clear()

        await ctx.send(f'{emoji.success} **Queue has been cleared**')

    @commands.command(name="loop", aliases=['l', 'repeat', 'rp'])
    async def _loop(self, ctx: commands.Context):
        """
        Loop current track
        """
        if not self.player.voice.is_playing():
            return await ctx.send(f'{emoji.failure} **Nothing is playing now**')

        self.player.loop = not self.player.loop

        if self.player.loop:
            await ctx.send(f'{emoji.success} **Track is set to repeat**')
        else:
            await ctx.send(f'{emoji.success} **Repetition removed**')

    async def search(self, query):
        loop = asyncio.get_event_loop()
        partial = functools.partial(self.ytdl.extract_info, query, download=False)
        search_data = await loop.run_in_executor(None, partial)

        if 'entries' not in search_data:
            result = search_data
        else:
            result = search_data['entries'].pop(0)

        return result

    @staticmethod
    async def send_embed(ctx: commands.Context, query: str, result: dict, voice):
        if voice.is_playing():
            message = f"""
            {emoji.youtube_icon} **Searching** {emoji.magnifier} `{query}`\n**Added to the queue** {emoji.notes} `{result}`
            """
        else:
            message = f"""
            {emoji.youtube_icon} **Searching** {emoji.magnifier} `{query}`\n**Playing** {emoji.notes} `{result}`
            """
        await ctx.send(message)

    @commands.command(name="create")
    async def _create(self, ctx: commands.Context, name: str):
        guild = ctx.guild
        Playlist.create(guild.id, name)

    @commands.command(name="add")
    async def _add(self, ctx: commands.Context, playlist, url):
        appender = ctx.author
        result = await self.search(url)
        data = {
            "title": result['title'],
            "date": datetime.now().__str__(),
            "appender": appender.id.__str__()
        }
        Playlist.add_track(ctx.guild.id, playlist, data)


class Player:

    def __init__(self, ctx: commands.Context, bot: commands.Bot):
        self.bot = bot
        self.ctx = ctx
        self.guild_id = ctx.guild.id
        self.current = None
        self.voice = None
        self.queue = TrackQueue()
        self.next = asyncio.Event()
        self.loop = False
        self.main_loop = self.bot.loop.create_task(self.player_loop())

    def __del__(self):
        self.main_loop.cancel()

    async def player_loop(self):
        while True:

            self.next.clear()

            if not self.loop:

                try:
                    async with timeout(180):
                        self.current = await self.queue.get()
                except asyncio.TimeoutError:
                    # Dont disconnect from channel when use loop, why ???
                    self.bot.loop.create_task(self.stop())
                    return

            self.voice.play(await self.current.create_source(), after=self.next_song)

            await self.next.wait()

    def next_song(self, error=None):
        self.next.set()

    async def stop(self):
        self.queue.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

        del self.ctx.cog.players[self.guild_id]


class Track:

    def __init__(self, url, title):
        self.url = url
        self.title = title

    async def create_source(self):
        return discord.FFmpegPCMAudio(self.url, **settings.FFMPEG_OPTIONS)


class TrackQueue(asyncio.Queue):

    def clear(self):
        self._queue.clear()

    def remove(self, index: int):
        del self._queue[index]

    def __len__(self):
        return self.qsize()

    def __getitem__(self, index: int):
        return self._queue[index]

    def __iter__(self):
        return self._queue.__iter__()


class Playlist:

    @staticmethod
    def create(guild_id: int, name: str):
        with open(f'{guild_id}_{name}.json') as file:
            json.dump([], file, indent=4)

    @staticmethod
    def add_track(guild_id, name: str, row: dict):
        with open(f'{guild_id}_{name}.json', 'r') as file:
            data = json.load(file)

        data.append(row)

        with open(f'{guild_id}_{name}.json', 'w') as file:
            json.dump(data, file, indent=4)
