from __future__ import annotations

import json
import random
import re
import urllib.parse

import aiohttp
import discord
from discord.ext import commands

from configuration import API_KEY, MAIN_CHANNEL_ID, SEARCH_ENGINE_ID


class Google(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def check_restricted_content(message):
        restricted_content = re.search(r'[\w\s]*(?:(?:[тt]+[rр]+[аa]+[нn]+[сc]+[ыe]+)|'
                                       r'(?:(?:(?:баб[ыа])|(?:тян)|(?:женщина[ыа])|(?:девушк[иа])) с '
                                       r'(?:(?:ху[яе]ми*)|(?:членом)|(?:письк(?:(?:ой)|(?:ами)))))'
                                       r'|(?:трасвиститы*))[\w\s]*', message, re.I)
        return restricted_content

    @commands.cooldown(1, 17, commands.BucketType.user)
    @commands.command(aliases=['image', 'img'])
    async def i(self, ctx, *, message):     # get random photo from google
        await ctx.message.delete()
        if ctx.channel.id == MAIN_CHANNEL_ID:
            if self.check_restricted_content(message):
                return await ctx.send('На терретории данного канала в соответсвии со Ст. 6.21 КоАП РФ.'
                                      'пропоганда баб с письками запрещена. Но вы всегда можете '
                                      'почертить в автокаде, например.')

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(message) +
                "&start=" + '1' + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID + "&searchType=image")
            result = json.loads(await resp.text())

        try:
            query_length = len(result['items'])
        except Exception:
            return await ctx.send('По данному запросу ничего не найдено. '
                                  'Попробуйте использовать более общий запрос.'
                                  )

        if query_length < 1:
            return await ctx.send('По данному запросу ничего не найдено. '
                                  'Попробуйте использовать более общий запрос.'
                                  )
        random_number = random.randint(0, query_length-1)
        await ctx.send(urllib.parse.unquote(result['items'][random_number]['link']))
        await ctx.send("Картинка по запросу: \"" + message + "\"")

    @staticmethod
    def parse_output_links(message) -> tuple[str, int]:
        if message[-1].isdigit():
            output_links = max(0, int(message[-1]))
            message = message[:-1].strip()
        else:
            output_links = 0
        return message, output_links

    @commands.command()
    async def g(self, ctx, *, query: str):
        """Google web search. Ex: [p]g what is discordapp?"""
        await ctx.message.delete()
        query, output_links_quantity = self.parse_output_links(query)

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                                "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(query) +
                                "&start=1" + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID)
            result = json.loads(await resp.text())

        if output_links_quantity == 0:
            await ctx.send(urllib.parse.unquote(result['items'][output_links_quantity]['link']))
            await ctx.send("Ссылка по запросу: \"" + query + "\"")
        else:
            info = discord.Embed(title=f'Ссылки по запросу {query}', color=discord.Color.green())
            for link_number in range(output_links_quantity):
                info.add_field(name=str(link_number+1),
                               value=urllib.parse.unquote(result['items'][link_number]['link']),
                               inline=False
                               )
            await ctx.send(embed=info)
