import requests
import re

from discord.ext import commands

import settings


class Notification(commands.Cog):

    @commands.command(name='report')
    async def _report(self, ctx: commands.Context, *, message: str):
        """
        Send message by telegram bot to user
        """
        user_ids = re.findall(r'<.*>', message)

        if user_ids:
            for id_ in user_ids:
                id__ = re.findall(r'<\W*(\d*)>', id_)[0]
                if id__ in settings.telegram_nick:
                    message = message.replace(id_, settings.telegram_nick.get(id_))

        api_url = f'https://api.telegram.org/bot{settings.telegram_token}/sendMessage'
        author = ctx.author
        params = {
            'chat_id': settings.chat_id,
            'text': f'Author: {author.name}\n'
                    f'Message: {message}'
        }
        requests.post(api_url, params)
