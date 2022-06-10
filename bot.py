import asyncio
import json

import settings
from loguru import logger

import discord
from discord.ext import commands

from discord_bot.music import MusicPlayer
from discord_bot.utils.websocket import WebSocket
from discord_bot.notification import Notification

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), enable_debug_events=True)
logger.add("../logs/discord_bot.log", rotation="50 MB", compression="zip", level="DEBUG")


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')


@bot.event
async def on_socket_raw_receive(msg):
    logger.debug(json.dumps(json.loads(msg), indent=4, ensure_ascii=False))


@bot.command(name="send")
async def _send(ctx: commands.Context, *, query: str):
    """
    Send query by bot
    """
    await ctx.send(query)

websocket = WebSocket('127.0.0.1', 5001)


@websocket.add_event
async def play(data):
    from discord_bot.music import Track
    user_id = data.get('user')
    query = data.get('query')
    author = bot.get_user(user_id)
    for voice_channel in [voice_channel for guild in author.mutual_guilds for voice_channel in guild.voice_channels]:
        if author in voice_channel.members:
            guild = voice_channel.guild
            break
    author = guild.get_member(user_id)
    channel = guild.text_channels[0]
    await bot.cogs['MusicPlayer'].prepare_voice_client(channel, author)
    result = await bot.cogs['MusicPlayer'].search(query)
    track = Track(result['webpage_url'], result['title'], result['duration'])
    await bot.cogs['MusicPlayer'].player.queue.put(track)
    return json.dumps({"message": "Success"})


@websocket.add_event
async def get_guilds():
    guilds = bot.guilds
    response = [
        {
            "id": guild.id,
            "name": guild.name,
            "owner": guild.owner.name,
            "member_count": guild.member_count,
            "icon": guild.icon.with_size(128).url if guild.icon else None,
            "members": [
                {
                    "login": member.name,
                    "nickname": member.nick,
                } for member in guild.members
            ],
        }
        for guild in guilds
    ]
    return json.dumps(response, ensure_ascii=False)


async def main():
    # async with websocket: # Need define __aexit__ method
    #     await websocket.serve()
    await websocket.serve()
    async with bot:
        await bot.add_cog(MusicPlayer(bot))
        await bot.add_cog(Notification())
        await bot.start(settings.BOT_TOKEN)


if __name__ == '__main__':
    asyncio.run(main())
