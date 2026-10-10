from __future__ import annotations

import asyncio
import json
import random
import re
import urllib.parse

import aiohttp
import discord
from discord import app_commands, errors
from discord.ext import commands

from app.configuration import API_KEY, MAIN_CHANNEL_ID, MY_GUILD, SEARCH_ENGINE_ID

IMAGE_CHECK_TIMEOUT = aiohttp.ClientTimeout(total=2)


class Google(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def check_restricted_content(message):
        restricted_content = re.search(
            r"[\w\s]*(?:(?:[тt]+[rр]+[аa]+[нn]+[сc]+[ыe]+)|"
            r"(?:(?:(?:баб[ыа])|(?:тян)|(?:женщина[ыа])|(?:девушк[иа])) с "
            r"(?:(?:ху[яе]ми*)|(?:членом)|(?:письк(?:(?:ой)|(?:ами)))))"
            r"|(?:трасвиститы*))[\w\s]*",
            message,
            re.I,
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

        if (
            MAIN_CHANNEL_ID
            and ctx.channel.id == MAIN_CHANNEL_ID
            and self.check_restricted_content(message)
        ):
            return await ctx.send(
                "На территории данного канала в соответствии со Ст. 6.21 КоАП РФ."
                "пропаганда баб с письками запрещена. Но вы всегда можете "
                "почертить в автокаде, например.",
            )

        # Google request + image checks can take longer than 3s for slash command response
        await ctx.defer()

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                "https://www.googleapis.com/customsearch/v1?q="
                + urllib.parse.quote_plus(message)
                + "&start="
                + "1"
                + "&key="
                + API_KEY
                + "&cx="
                + SEARCH_ENGINE_ID
                + "&searchType=image",
            )
            result = json.loads(await resp.text())

            items = result.get("items") or []
            if not items:
                return await ctx.send(
                    "По данному запросу ничего не найдено. Попробуйте использовать более общий запрос.",
                )

            links = [item["link"] for item in items]
            checks = await asyncio.gather(
                *(self.is_image_available(session, link) for link in links),
            )

        available_links = [link for link, is_available in zip(links, checks) if is_available]
        if available_links:
            link = random.choice(available_links)
        else:
            # Google thumbnails are hosted on gstatic and almost always load
            item = random.choice(items)
            link = item.get("image", {}).get("thumbnailLink") or item["link"]

        await ctx.send(link)
        await ctx.channel.send('Картинка по запросу: "' + message + '"')

    @staticmethod
    async def is_image_available(session: aiohttp.ClientSession, url: str) -> bool:
        try:
            async with session.get(url, timeout=IMAGE_CHECK_TIMEOUT) as resp:
                return resp.status == 200 and resp.content_type.startswith("image/")
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return False

    @app_commands.command(name="g", description="Сделать запрос к Google")
    @commands.cooldown(1, 17)
    @app_commands.guilds(MY_GUILD)
    async def g(self, interaction: discord.Interaction, links_amount: int = 0, *, query: str):
        """Google web search. Ex: [p]g what is discordapp?"""

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                "https://www.googleapis.com/customsearch/v1?q="
                + urllib.parse.quote_plus(query)
                + "&start=1"
                + "&key="
                + API_KEY
                + "&cx="
                + SEARCH_ENGINE_ID,
            )
            result = json.loads(await resp.text())

        try:
            result["items"]
        except KeyError:
            return await interaction.response.send_message(
                "По данному запросу ничего не найдено. Попробуйте использовать более общий запрос.",
            )

        if links_amount == 0:
            await interaction.response.send_message(
                urllib.parse.unquote(result["items"][links_amount]["link"]),
            )
            await interaction.channel.send('Ссылка по запросу: "' + query + '"')
        else:
            info = discord.Embed(title=f"Ссылки по запросу {query}", color=discord.Color.green())
            for link_number in range(links_amount):
                info.add_field(
                    name=str(link_number + 1),
                    value=urllib.parse.unquote(result["items"][link_number]["link"]),
                    inline=False,
                )
            await interaction.response.send_message(embed=info)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Google(bot), guild=MY_GUILD)
