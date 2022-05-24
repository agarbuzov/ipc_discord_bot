import requests
import re

import settings

from discord.ext import commands


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
                if id__ in settings.TELEGRAM_NICK:
                    message = message.replace(id_, settings.TELEGRAM_NICK.get(id__))

        api_url = f'https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage'
        author = ctx.author
        params = {
            'chat_id': settings.CHAT_ID,
            'text': f'Author: {author.name}\n'
                    f'Message: {message}'
        }
        requests.post(api_url, params)
