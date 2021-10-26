import asyncio
import functools

import discord
from discord.ext import commands
from utils import emoji
import youtube_dl

import settings

# TODO fix One queue for all servers
# TODO add move to if guild.id=guild.id
# TODO multi use command play from one user -> Nonetype search
# TODO something 403 in search
# TODO Validators
# TODO Split play command
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
            await ctx.channel.send(f'{emoji.failure} **No data passed**')
            return

        voice_client = ctx.guild.voice_client

        if not voice_client:
            # if not connected to some guild channel -> connect to author voice channel
            author_voice_state = ctx.author.voice

            if not author_voice_state:
                # if user not connected to some voice channel
                await ctx.channel.send(f'{emoji.failure} **You are not connected to any voice channel on guild**')
                return

            voice_client = await author_voice_state.channel.connect()

        elif voice_client and voice_client.channel.id != ctx.author.voice.channel.id:
            # if user in another voice channel -> move to him voice channel
            await voice_client.move_to(ctx.author.voice.channel)

        result = await self.search(query)

        await self.send_embed(ctx, query, result['title'], voice_client)

        player = self.players.get(ctx.guild.id)

        if not player:
            player = Player(self.bot)
            self.players[ctx.guild.id] = player

        player.voice = voice_client
        source = discord.FFmpegPCMAudio(result['url'], **settings.FFMPEG_OPTIONS)
        source.title = result['title']
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

    @commands.command(name="pause")
    async def _pause(self, ctx: commands.Context):
        """
        Pause current track
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{emoji.failure} **Bot is not connected to any voice channel on guild**')
            return

        if voice_client.is_paused():
            await ctx.send(f'{emoji.failure} **Already paused**')
            return

        voice_client.pause()
        await ctx.send(f'{emoji.pause_button} **Paused**')

    @commands.command(name="resume")
    async def _resume(self, ctx: commands.Context):
        """
        Resume current track
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{emoji.failure} **Bot is not connected to any voice channel on guild**')
            return

        if voice_client.is_playing():
            await ctx.send(f'{emoji.failure} **Already playing**')
            return

        voice_client.resume()
        await ctx.send(f'{emoji.pause_button} **Resumed**')

    @commands.command(name="next", aliases=['skip'])
    async def _next(self, ctx: commands.Context):
        """
        Skip current track in queue
        """
        player = self.players.get(ctx.guild.id)

        if not player.voice:
            await ctx.send(f'{emoji.failure} **Bot is not connected to any voice channel on guild**')
            return

        if not (player.voice.is_paused() or player.voice.is_playing()):
            await ctx.send(f'{emoji.failure} **Nothing to skip**')
            return

        player.voice.stop()
        await ctx.send(f'{emoji.next_track} **Skipped**')
        if player.voice.is_playing() and player.current:
            await ctx.send(f'{emoji.youtube_icon} **Playing** `{player.current.title}`')

    @commands.command(name="now")
    async def _now(self, ctx: commands.Context):
        """
        Get current track
        """
        player = self.players.get(ctx.guild.id)

        if not player.voice.is_playing():
            await ctx.send(f'{emoji.failure} **Nothing is playing now**')
            return

        await ctx.send(f'{emoji.play_pause} `{player.current.title}` **is playing now**')

    @commands.command(name='queue', parent='Queue')
    async def _queue(self, ctx: commands.Context):
        """
        Get list of track in queue
        """
        player = self.players.get(ctx.guild.id)

        queue = ''
        for i, track in enumerate(player.queue):
            queue += f'{i+1}.{track.title}\n'

        embed = discord.Embed(title=f'{emoji.notes} {len(player.queue)} tracks in queue',
                              description=f'{queue}')
        await ctx.send(embed=embed)

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """
        Remove track from queue by index
        """
        player = self.players.get(ctx.guild.id)

        if player.queue == 0:
            await ctx.send(f'{emoji.failure} **Queue is empty**')
            return

        player.queue.remove(index - 1)
        await ctx.send(f'{emoji.success} `{player.queue[index - 1].title}` **removed from queue**')

    @commands.command(name='clear')
    async def _clear(self, ctx: commands.Context):
        """
        Clear the queue
        """
        player = self.players.get(ctx.guild.id)

        if len(player.queue) == 0:
            await ctx.send(f'{emoji.failure} **Queue is empty**')
            return

        player.queue.clear()
        await ctx.send(f'{emoji.success} **Queue has been cleared**')

    @commands.command(name="stop")
    async def _stop(self, ctx: commands.Context):
        """
        Clear queue and stop playing
        """
        player = self.players.get(ctx.guild.id)

        if player.queue > 0:
            player.queue.clear()

        player.voice.stop()
        await ctx.send(f'{emoji.stop_button} **Stopped**')

    @commands.command(name="send")
    async def _send(self, ctx: commands.Context, *, query: str):
        """
        Send query by bot
        """
        print(query)
        await ctx.send(query)

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


class Player:

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current = None
        self.voice = None
        self.queue = TrackQueue()
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
