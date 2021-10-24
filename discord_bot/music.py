import asyncio
import functools

import discord
from discord.ext import commands

import youtube_dl

import settings


class MusicPlayer(commands.Cog):

    def __init__(self):
        self.ytdl = youtube_dl.YoutubeDL(settings.YTDL_OPTIONS)

    @commands.command(name="play")
    async def _play(self, ctx: commands.Context, *, query: str):
        """
        Play youtube track
        """
        if not query:
            await ctx.channel.send(f'{settings.prefix_emoji} **No data passed**')
            return

        voice_client = ctx.guild.voice_client

        if voice_client:

            if voice_client.is_playing():
                """add track to queue"""
                await ctx.channel.send(f'{settings.prefix_emoji} **Bot already playing. Queue not ready now**')
                return

        else:
            author_voice_state = ctx.author.voice

            if not author_voice_state:
                await ctx.channel.send(f'{settings.prefix_emoji} **You are not connected to any voice channel on guild**')
                return

            voice_client = await author_voice_state.channel.connect()

        result = await self.search(query)

        await self.send_embed(ctx, query, result['title'])

        voice_client.play(discord.FFmpegPCMAudio(result['url'], **settings.FFMPEG_OPTIONS))

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

    @commands.command(name="stop", aliases=['skip'])
    async def _stop(self, ctx: commands.Context):
        """
        Stop current track
        """
        voice_client = ctx.guild.voice_client

        if not voice_client:
            await ctx.send(f'{settings.prefix_emoji} **Bot is not connected to any voice channel on guild**')
            return

        if not (voice_client.is_paused() or voice_client.is_playing()):
            await ctx.send(f'{settings.prefix_emoji} **Nothing to stop**')
            return

        voice_client.stop()
        await ctx.send(f':stop_button: **Stopped**')

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

    @commands.command(name="next")
    async def _next(self, ctx: commands.Context):
        """
        Next track in queue
        If queue is empty -> ctx.send_message 'Queue is empty'
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

