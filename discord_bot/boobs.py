import requests
from bs4 import BeautifulSoup
from io import BytesIO
import discord
from discord.ext import commands


class Boobs(commands.Cog):

    @commands.command(name="boobs")
    async def _boobs(self, ctx: commands.Context):
        """
        Get random boobs
        """
        image = self.get_boobs()
        await ctx.send(file=discord.File(image, filename='boobs.png'))
        pass

    def get_boobs(self):
        # TODO if many commands boobs, they are not execute one by one but all at once
        boobs_src = self.parse_boobs()
        response = requests.get(boobs_src)
        img = BytesIO(response.content)
        return img

    @staticmethod
    def parse_boobs():
        response = requests.get('http://www.boobcritic.com/random-boobs/')
        data = BeautifulSoup(response.text, 'lxml')
        post = data.find(class_='post-content')
        boobs_src = post.find('img')['src']
        return boobs_src
