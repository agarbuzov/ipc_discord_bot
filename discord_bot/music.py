import asyncio
import functools

import discord
from discord.ext import commands

import youtube_dl

import settings

# TODO fix One queue for all servers
# TODO add move to if guild.id=guild.id
class MusicPlayer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)
        self.players = {}

    @commands.command(name="play")
    async def _play(self, ctx: commands.Context, *, query: str):
        """
        Play youtube track
        """
        if not query:
            await ctx.channel.send(f'{settings.prefix_emoji} **No data passed**')
            return

        voice_client = ctx.guild.voice_client

        if not voice_client:
            author_voice_state = ctx.author.voice

            if not author_voice_state:
                await ctx.channel.send(f'{settings.prefix_emoji} **You are not connected to any voice channel on guild**')
                return

            voice_client = await author_voice_state.channel.connect()

        result = await self.search(query)

        await self.send_embed(ctx, query, result['title'])

        player = self.players.get(ctx.guild.id)

        if not player:
            player = Player(self.bot)
            self.players[ctx.guild.id] = player

        player.voice = voice_client
        source = discord.FFmpegPCMAudio(result['url'], **settings.FFMPEG_OPTIONS)
        await player.queue.put(source)

    async def search(self, query):
        loop = asyncio.get_event_loop()
        partial = functools.partial(self.ytdl.extract_info, query, download=False)
        search_data = await loop.run_in_executor(None, partial)

        if 'entries' not in search_data:
            result = search_data
        else:
            result = search_data['entries'].pop(0)

        print(result)

        return result

    @commands.command(name="next", aliases=['skip'])
    async def _next(self, ctx: commands.Context):
        """
        Skip current track in queue
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{settings.prefix_emoji} **Bot is not connected to any voice channel on guild**')
            return

        if not (voice_client.is_paused() or voice_client.is_playing()):
            await ctx.send(f'{settings.prefix_emoji} **Nothing to skip**')
            return

        voice_client.stop()
        await ctx.send(f':next_track: **Skipped**')

    @commands.command(name="pause")
    async def _pause(self, ctx: commands.Context):
        """
        Pause current track
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{settings.prefix_emoji} **Bot is not connected to any voice channel on guild**')
            return

        if voice_client.is_paused():
            await ctx.send(f'{settings.prefix_emoji} **Already paused**')
            return

        voice_client.pause()
        await ctx.send(f':pause_button: **Paused**')

    @commands.command(name="resume")
    async def _resume(self, ctx: commands.Context):
        """
        Resume current track
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{settings.prefix_emoji} **Bot is not connected to any voice channel on guild**')
            return

        if voice_client.is_playing():
            await ctx.send(f'{settings.prefix_emoji} **Already playing**')
            return

        voice_client.resume()
        await ctx.send(f':play_pause: **Resumed**')

    @commands.command(name="stop")
    async def _stop(self, ctx: commands.Context):
        """
        Clean queue
        Stop playing
        """
        pass

    @commands.command(name="now")
    async def _now(self, ctx: commands.Context):
        """Current track in queue"""
        pass

    @commands.command(name="send")
    async def _send(self, ctx: commands.Context, *, query: str):
        """
        Send query by bot
        """
        print(query)
        await ctx.send(query)

    @staticmethod
    async def send_embed(ctx: commands.Context, query: str, result: dict):
        message = f"""
        {settings.prefix_emoji} **Searching** :mag_right: `{query}`\n**Playing** :notes: `{result}`
        """
        await ctx.send(message)

    # @commands.command(name='queue')
    # async def _queue(self, ctx: commands.Context):
    #     player = self.players.get(ctx.guild.id)
    #     await ctx.send(player.queue)


class Player:

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current = None
        self.voice = None
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.main_loop = self.bot.loop.create_task(self.player_loop())

    def __del__(self):
        self.main_loop.cancel()

    async def player_loop(self):
        while True:

            self.next.clear()

            self.current = await self.queue.get()

            self.voice.play(self.current, after=self.next_song)

            await self.next.wait()

    def next_song(self, error=None):
        self.next.set()
