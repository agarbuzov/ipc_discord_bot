import settings
from loguru import logger

import discord
from discord.ext import commands

from music import MusicPlayer
from notification import Notification

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
logger.add("discord_bot.log", rotation="50 MB", compression="zip", level="DEBUG")


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')


@bot.command(name="send")
async def _send(ctx: commands.Context, *, query: str):
    """
    Send query by bot
    """
    await ctx.send(query)

if __name__ == '__main__':
    bot.add_cog(MusicPlayer(bot))
    bot.add_cog(Notification())
    bot.run(settings.bot_token)
