from __future__ import annotations

import json
import random
import re
import urllib.parse

import aiohttp
import discord
from discord import app_commands, errors
from discord.ext import commands

from configuration import API_KEY, MAIN_CHANNEL_ID, SEARCH_ENGINE_ID, MY_GUILD


class Google(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def check_restricted_content(message):
        restricted_content = re.search(
            r"[\w\s]*(?:(?:[тt]+[rр]+[аa]+[нn]+[сc]+[ыe]+)|"
            r"(?:(?:(?:баб[ыа])|(?:тян)|(?:женщина[ыа])|(?:девушк[иа])) с "
            r"(?:(?:ху[яе]ми*)|(?:членом)|(?:письк(?:(?:ой)|(?:ами)))))"
            r"|(?:трасвиститы*))[\w\s]*", message, re.I
        )
        return restricted_content

    @commands.hybrid_command(name="i", description="Получить случайное изображение")
    @commands.cooldown(1, 17)
    @app_commands.guilds(MY_GUILD)
    async def i(self, ctx: commands.Context, *, message: str):  # get random photo from google api
        try:
            await ctx.message.delete()
        except errors.NotFound:
            pass

        if ctx.channel.id == MAIN_CHANNEL_ID and self.check_restricted_content(message):
            return await ctx.send(
                "На терретории данного канала в соответсвии со Ст. 6.21 КоАП РФ."
                "пропоганда баб с письками запрещена. Но вы всегда можете "
                "почертить в автокаде, например."
            )

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(message) +
                "&start=" + "1" + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID + "&searchType=image"
            )
            result = json.loads(await resp.text())

        try:
            query_length = len(result["items"])
        except Exception:
            return await ctx.send(
                "По данному запросу ничего не найдено.Попробуйте использовать более общий запрос."
            )

        if query_length < 1:
            return await ctx.send(
                "По данному запросу ничего не найдено. Попробуйте использовать более общий запрос."
            )
        random_number = random.randint(0, query_length-1)
        await ctx.send(f"{urllib.parse.unquote(result['items'][random_number]['link'])} ")
        await ctx.channel.send("Картинка по запросу: \"" + message + "\"")

    @app_commands.command(name="g", description="Сделать запрос к Google")
    @commands.cooldown(1, 17)
    @app_commands.guilds(MY_GUILD)
    async def g(self, interaction: discord.Interaction, links_amount: int = 0, *, query: str):
        """Google web search. Ex: [p]g what is discordapp?"""

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(query) +
                "&start=1" + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID
            )
            result = json.loads(await resp.text())

        try:
            result["items"]
        except KeyError:
            return await interaction.response.send_message(
                "По данному запросу ничего не найдено. Попробуйте использовать более общий запрос."
            )

        if links_amount == 0:
            await interaction.response.send_message(
                urllib.parse.unquote(result["items"][links_amount]["link"])
            )
            await interaction.channel.send("Ссылка по запросу: \"" + query + "\"")
        else:
            info = discord.Embed(title=f"Ссылки по запросу {query}", color=discord.Color.green())
            for link_number in range(links_amount):
                info.add_field(
                    name=str(link_number+1),
                    value=urllib.parse.unquote(result["items"][link_number]["link"]),
                    inline=False
                )
            await interaction.response.send_message(embed=info)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Google(bot), guild=MY_GUILD)
