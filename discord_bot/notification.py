import requests

from discord.ext import commands

import settings


class Notification(commands.Cog):

    @commands.command(name='report')
    async def _report(self, ctx: commands.Context, *, message: str):
        """
        Send message by telegram bot to user
        """
        api_url = f'https://api.telegram.org/bot{settings.telegram_token}/sendMessage'
        guild = ctx.guild
        author = ctx.author
        params = {
            'chat_id': settings.chat_id,
            'text': f'Author: {author.name}#{author.discriminator}\n'
                    f'Guild: {guild.name}#{guild.id}\n'
                    f'Message: {message}'
        }
        requests.post(api_url, params)
