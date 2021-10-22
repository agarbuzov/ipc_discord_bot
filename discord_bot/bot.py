import asyncio
import functools
import itertools
import math
import random

import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')


class MusicPlayer(commands.Cog):
    def __init__(self):
        self.bot = bot

    @commands.command()
    async def play(self, ctx: commands.Context, query: str):

        if not query:
            await ctx.channel.send('No data passed')
            return

        voice_state = ctx.author.voice

        # if not voice_state:
        #     await ctx.channel.send('You are not connected to any voice channel on guild')
        #     return
        # else:
        #     pass
        #     """
        #     Add to queue
        #     """


        self.voice_client = await voice_state.channel.connect()

        search_data = ytdl.extract_info(query, download=False)

        result = search_data['entries'].pop(0)['url']

        self.voice_client.play(discord.FFmpegPCMAudio(result, **FFMPEG_OPTIONS))
        """
        if not voice_state on this guild -> connect to ctx.message.user.voice_channel, else -> just play
        if already playing -> add to queue 
        """

    @commands.command()
    async def pause(self, ctx: commands.Context):
        self.voice_client.pause()
        pass
        """
        if not already playing -> ctx.send_message('Not connected to any voice channel')
        if playing -> pause 
        is_paused -> True
        How resolve with get bytes from ytdl ?
        """

    @commands.command()
    async def resume(self, ctx: commands.Context):
        self.voice_client.resume()
        """
        if not is_paused -> ctx.send_message 'nothing for resume'
        """
        pass

    @commands.command()
    async def next(self, ctx: commands.Context):
        """
        If queue is empty -> ctx.send_message 'Queue is empty'
        """
        pass

    @commands.command()
    async def now(self, ctx: commands.Context):
        pass

    @commands.command()
    async def connect(self, ctx: commands.Context):

        pass

    @commands.command()
    async def disconnect(self, ctx: commands.Context):
        pass


    async def send_embed(self):
        pass


bot.add_cog(MusicPlayer())

if __name__ == '__main__':
    bot.run('NzY5OTk1MTAzNTM2MTUyNTk3.X5XH0g.BlSS-CbJCxvioH3ImuVlXXU7Oko')