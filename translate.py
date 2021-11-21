import aiohttp
import discord

from bs4 import BeautifulSoup
from discord.ext import commands


headers_Get = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }


@commands.command(pass_context=True)
async def trans(ctx, to_language, *, msg):
    """Translates words from one language to another. Do [p]help translate for more information.
    Usage:
    [p]translate <new language> <words> - Translate words from one language to another. Full language names must be used.
    The original language will be assumed automatically.
    """

    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            "https://gist.githubusercontent.com/astronautlevel2/93a19379bd52b351dbc6eef269efa0bc/raw/18d55123bc85e2ef8f54e09007489ceff9b3ba51/langs.json"
        )
        lang_codes = await resp.json(content_type='text/plain')
    real_language = False
    to_language = to_language.lower()
    if to_language in ["rus", "ru"]:
        to_language = 'russian'
    elif to_language in ["eng", "en"]:
        to_language = 'english'
    elif to_language == 'ukr':
        to_language = 'ukrainian'
    for entry in lang_codes:

        if to_language in lang_codes[entry]["name"].replace(";", "").replace(",", "").lower().split() \
           or to_language == entry:
            language = lang_codes[entry]["name"].replace(";", "").replace(",", "").split()[0]
            to_language = entry
            real_language = True

    if real_language:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                    "https://translate.google.com/m",
                    params={"hl": to_language, "sl": "auto", "q": msg},
                    headers=headers_Get
            )
            translate = await resp.text()
            result = str(translate).split('class="t0">')[1].split("</div>")[0]
            result = BeautifulSoup(result, "lxml").text
            embed = discord.Embed(color=discord.Color.blue())
            embed.add_field(name="Original", value=msg, inline=False)
            embed.add_field(name=language, value=result.replace("&amp;", "&"), inline=False)
            if result == msg:
                embed.add_field(name="Warning", value="This language may not be supported by Google Translate.")
            await ctx.send("", embed=embed)
    else:
        await ctx.send("That's not a real language.")
