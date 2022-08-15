import asyncio
import json

import discord
import settings

from discord.ext.commands import Bot
from discord_bot.websocket import WebSocket
from discord_bot.notification import Notifications

bot = Bot(command_prefix="!", intents=discord.Intents.all())
websocket = WebSocket("localhost", 5005)


@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')


@websocket.add_event
async def send_notification():
    await bot.cogs['Notifications'].send_notification(63813769)


@websocket.add_event
async def bot_info():
    return json.dumps({
        "id": bot.user.id,
        "name": bot.user.name,
        "avatar": bot.user.avatar.with_size(256).url
    })


async def main():
    await websocket.serve()
    async with bot:
        await bot.add_cog(Notifications(bot))
        await bot.start(settings.BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
