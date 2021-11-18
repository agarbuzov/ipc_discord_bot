import asyncio
import inflect
import discord
import datetime
import settings
import functools
import youtube_dl

from typing import Optional
from loguru import logger
from async_timeout import timeout
from discord.ext import commands
from utils import emoji

ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)


def validation(func):

    async def wrapper(self, ctx):

        if not self.voice_client:
            return await ctx.send(f'{emoji.failure} **Bot is not connected to any voice channel on guild**',
                                  delete_after=5)

        return await func(self, ctx)
    return wrapper


class MusicPlayer(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = dict()
        self.player: Optional[Player] = None
        self.voice_client: Optional[discord.VoiceClient] = None

    async def cog_before_invoke(self, ctx: commands.Context):

        self.player: Player = self.players.get(ctx.guild.id)

        self.voice_client: discord.VoiceProtocol = ctx.guild.voice_client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.player and self.voice_client and self.player.message and message.id != self.player.message.id and\
                message.channel == self.player.message.channel:
            await self.player.resend_message()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member,
                                    before: discord.VoiceState, after: discord.VoiceState):
        if member == self.bot.user:
            if after.channel is None:
                await self.player.stop()

    @commands.command(name="play")
    @logger.catch
    async def _play(self, ctx: commands.Context, *, query: str):
        """
        Play youtube track
        """
        with ctx.typing():

            if not query:
                return await ctx.channel.send(f'{emoji.failure} **No data passed**', delete_after=5)

            if not self.voice_client:
                # if not connected to some guild channel -> connect to author voice channel
                author_voice_state = ctx.author.voice

                if not author_voice_state:
                    # if user not connected to some voice channel
                    return await ctx.channel.send(f'{emoji.failure} '
                                                  f'**You are not connected to any voice channel on guild**',
                                                  delete_after=5)

                self.voice_client = await author_voice_state.channel.connect()

            elif self.voice_client and self.voice_client.channel.id != ctx.author.voice.channel.id:
                # if user in another voice channel -> move to him voice channel
                await self.voice_client.move_to(ctx.author.voice.channel)

            result = await self.search(query)

            if not self.player:
                self.player = Player(ctx, self.bot)
                self.players[ctx.guild.id] = self.player

            self.player.voice = self.voice_client

            track = Track(result['webpage_url'], result['title'], result['duration'])

            await self.player.queue.put(track)
            await ctx.message.delete(delay=5)
            await self.send_embed(ctx, query, result['title'], self.voice_client)

    @commands.command(name="pause", aliases=['p'])
    @validation
    async def _pause(self, ctx: commands.Context):
        """
        Pause current track
        """
        if self.voice_client.is_paused():
            return await ctx.send(f'{emoji.failure} **Already paused**', delete_after=5)

        self.voice_client.pause()
        await ctx.send(f'{emoji.pause_button} **Paused**', delete_after=5)

    @commands.command(name="resume", aliases=['r'])
    @validation
    async def _resume(self, ctx: commands.Context):
        """
        Resume current track
        """
        if self.voice_client.is_playing():
            return await ctx.send(f'{emoji.failure} **Already playing**', delete_after=5)

        self.voice_client.resume()
        await ctx.send(f'{emoji.pause_button} **Resumed**', delete_after=5)

    @commands.command(name="stop", aliases=['s'])
    @validation
    async def _stop(self, ctx: commands.Context):
        """
        Clear queue and stop playing
        """
        self.player.loop = False

        if len(self.player.queue) > 0:
            self.player.queue.clear()

        self.player.voice.stop()

        await ctx.send(f'{emoji.stop_button} **Stopped**', delete_after=5)

    @commands.command(name='queue', aliases=['q', 'que'])
    async def _queue(self, ctx: commands.Context):
        """
        Get list of track in queue
        """
        player = self.players.get(ctx.guild.id)
        corrector = inflect.engine()
        queue = ''

        for i, track in enumerate(player.queue):
            queue += f'{i+1}.{track.title} {track.duration}\n'

        embed = discord.Embed(title=f'{emoji.notes} {len(player.queue)}'
                                    f' {corrector.plural("track", len(player.queue))} in queue',
                              description=f'{queue}')
        await ctx.message.delete(delay=5)
        await ctx.send(embed=embed)

    @commands.command(name="next", aliases=['skip', 'nx', 'sk'])
    @validation
    async def _next(self, ctx: commands.Context):
        """
        Skip current track in queue
        """
        if not (self.player.voice.is_paused() or self.player.voice.is_playing()):
            return await ctx.send(f'{emoji.failure} **Nothing to skip**', delete_after=5)

        self.player.loop = False

        self.player.voice.stop()
        await ctx.send(f'{emoji.next_track} **Skipped**', delete_after=5)
        if self.player.voice.is_playing() and self.player.current:
            await ctx.send(f'{emoji.youtube_icon} **Playing** `{self.player.current.title}`', delete_after=5)

    @commands.command(name="now")
    async def _now(self, ctx: commands.Context):
        """
        Get current track
        """
        if not self.player.voice.is_playing():
            return await ctx.send(f'{emoji.failure} **Nothing is playing now**', delete_after=5)

        await ctx.send(f'{emoji.play_pause} `{self.player.current.title}` **is playing now**', delete_after=5)

    @commands.command(name='remove', aliases=['rm'])
    async def _remove(self, ctx: commands.Context, index: int):
        """
        Remove track from queue by index
        """
        if self.player.queue == 0:
            return await ctx.send(f'{emoji.failure} **Queue is empty**', delete_after=5)

        self.player.queue.remove(index - 1)
        await ctx.send(f'{emoji.success} `{self.player.queue[index - 1].title}` **removed from queue**', delete_after=5)

    @commands.command(name='clear', aliases=['cl'])
    async def _clear(self, ctx: commands.Context):
        """
        Clear the queue
        """
        if len(self.player.queue) == 0:
            return await ctx.send(f'{emoji.failure} **Queue is empty**', delete_after=5)

        self.player.queue.clear()

        await ctx.send(f'{emoji.success} **Queue has been cleared**', delete_after=5)

    @commands.command(name="loop", aliases=['l', 'repeat', 'rp'])
    async def _loop(self, ctx: commands.Context):
        """
        Loop current track
        """
        if not self.player.voice.is_playing():
            return await ctx.send(f'{emoji.failure} **Nothing is playing now**', delete_after=5)

        self.player.loop = not self.player.loop

        if self.player.loop:
            message = f'{emoji.success} **Track is set to repeat**'
        else:
            message = f'{emoji.success} **Repetition removed**'
        await ctx.send(message, delete_after=5)

    @logger.catch
    async def search(self, query: str):
        partial = functools.partial(ytdl.extract_info, query, download=False)
        search_data = await self.bot.loop.run_in_executor(None, partial)

        if 'entries' not in search_data:
            result = search_data
        else:
            result = search_data['entries'].pop(0)

        return result

    @staticmethod
    async def send_embed(ctx: commands.Context, query: str, result: dict, voice):
        if voice.is_playing() or voice.is_paused():
            message = f'{emoji.youtube_icon} **Searching** {emoji.magnifier} ' \
                      f'`{query}`\n**Added to the queue** {emoji.notes} `{result}`'
        else:
            message = f'{emoji.youtube_icon} **Searching** {emoji.magnifier} ' \
                      f'`{query}`\n**Playing** {emoji.notes} `{result}`'
        await ctx.send(message, delete_after=5)


class Player:

    def __init__(self, ctx: commands.Context, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.ctx: commands.Context = ctx
        self.guild_id: int = ctx.guild.id
        self.current: Optional[Track] = None
        self.voice: Optional[discord.VoiceClient] = None
        self.queue = TrackQueue()
        self.next = asyncio.Event()
        self.loop: bool = False
        self.main_loop = self.bot.loop.create_task(self.player_loop())
        self.check_voice_members = self.bot.loop.create_task(self.check_members_loop())
        self.message: Optional[discord.Message] = None

    def __del__(self):
        self.main_loop.cancel()
        self.check_voice_members.cancel()

    @logger.catch
    async def check_members_loop(self):
        while True:
            logger.debug('check_members_loop')
            await asyncio.sleep(180)
            if len(self.voice.channel.members) == 1 and self.bot.user in self.voice.channel.members:
                await self.stop()

    @logger.catch
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
            # self.voice.play(self.current.create_source(self.bot.loop), after=self.next_song)
            source = await self.current.create_source(self.bot.loop)
            logger.debug(source)
            self.voice.play(source, after=self.next_song)

            if not self.message:
                await self.send_message()
            elif self.message.id != self.ctx.channel.last_message_id:
                await self.resend_message()
            # elif self.loop:
            #     pass
            else:
                await self.edit_message()

            await self.next.wait()

    def next_song(self, error=None):
        self.next.set()

    async def send_message(self):
        # if not message with player
        self.message = await self.ctx.send(f'{emoji.play_pause} `{self.current.title}` **is playing now**\n'
                                           f'{emoji.clock} **Duration**: `{self.current.duration}`',
                                           view=PlayView(self))
        logger.debug(self.message)

    @logger.catch
    async def resend_message(self):
        # if message with player isn't last on channel
        self.message = await self.message.delete()
        self.message = await self.ctx.send(f'{emoji.play_pause} `{self.current.title}` **is playing now**\n'
                                           f'{emoji.clock} **Duration**: `{self.current.duration}`',
                                           view=PlayView(self))
        logger.debug(self.message)

    async def edit_message(self):
        await self.message.edit(content=f'{emoji.play_pause} `{self.current.title}` **is playing now**\n'
                                        f'{emoji.clock} **Duration**: `{self.current.duration}`',
                                view=PlayView(self))
        logger.debug(self.message)

    @logger.catch
    async def stop(self):
        self.queue.clear()

        self.message = await self.message.delete()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

        self.main_loop.cancel()
        self.check_voice_members.cancel()

        del self.ctx.cog.players[self.guild_id]


class Track:

    def __init__(self, webpage_url: str, title: str, duration: int):
        self.webpage_url = webpage_url
        self.title = title
        self.duration = str(datetime.timedelta(seconds=duration))

    async def create_source(self, loop):
        partial = functools.partial(ytdl.extract_info, self.webpage_url, download=False)
        result = await loop.run_in_executor(None, partial)

        return discord.FFmpegPCMAudio(result['url'], **settings.FFMPEG_OPTIONS)


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


class PlayView(discord.ui.View):

    def __init__(self, player):
        super().__init__(timeout=None)
        self.add_item(self.Pause(player))
        self.add_item(self.Next(player))
        self.add_item(self.Repeat(player))

    class Pause(discord.ui.Button):
        def __init__(self, player: Player):
            self.player = player

            if self.player.voice.is_playing():
                self.action = self.player.voice.pause
                style = discord.ButtonStyle.secondary
            else:
                self.action = self.player.voice.resume
                style = discord.ButtonStyle.primary

            super().__init__(style=style, emoji=discord.PartialEmoji(name='⏯'))

        async def callback(self, interaction: discord.Interaction):
            self.action()
            await interaction.response.edit_message(view=PlayView(self.player))

    class Next(discord.ui.Button):
        def __init__(self, player: Player):
            self.player = player
            super().__init__(style=discord.ButtonStyle.secondary, emoji=discord.PartialEmoji(name='⏩'))

        async def callback(self, interaction: discord.Interaction):
            self.player.loop = False
            self.player.voice.stop()

    class Repeat(discord.ui.Button):
        def __init__(self, player: Player):
            self.player = player

            if not self.player.loop:
                style = discord.ButtonStyle.secondary
            else:
                style = discord.ButtonStyle.primary

            super().__init__(style=style, emoji=discord.PartialEmoji(name='🔁'))

        async def callback(self, interaction: discord.Interaction):
            self.player.loop = not self.player.loop
            await interaction.response.edit_message(view=PlayView(self.player))
