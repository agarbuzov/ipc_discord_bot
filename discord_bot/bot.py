import settings

import discord
from discord.ext import commands

from music import MusicPlayer

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')

if __name__ == '__main__':
    bot.add_cog(MusicPlayer(bot))
    bot.run(settings.bot_token)
