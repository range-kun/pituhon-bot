import aiohttp
import urllib.parse
import re
import random
import discord
import json

from discord.ext import commands
from configuration import API_KEY, MAIN_CHANNEL_ID, SEARCH_ENGINE_ID


@commands.cooldown(1, 17, commands.BucketType.user)
@commands.command(pass_context=True, aliases=['image', 'img'])
async def i(ctx, *, message):     # get random photo from google
    await ctx.message.delete()
    if ctx.channel.id == MAIN_CHANNEL_ID:
        restricted_content = re.search(r'[\w\s]*(?:(?:[тt]+[rр]+[аa]+[нn]+[сc]+[ыe]+)|'
                              r'(?:(?:(?:баб[ыа])|(?:тян)|(?:женщина[ыа])|(?:девушк[иа])) с '
                              r'(?:(?:ху[яе]ми*)|(?:членом)|(?:письк(?:(?:ой)|(?:ами)))))'
                              r'|(?:трасвиститы*))[\w\s]*', message, re.I)
        if restricted_content:
            return await ctx.send('На терретории данного канала в соответсвии со Ст. 6.21 КоАП РФ.'
                                  'пропоганда баб с письками запрещена. Но вы всегда можете '
                                  'почертить в автокаде, например.')
    async with aiohttp.ClientSession() as session:
        resp = await session.get(
            "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(message) +
            "&start=" + '1' + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID + "&searchType=image")
        result = json.loads(await resp.text())
        try:
            result['items']
        except Exception:
            return await ctx.send('По данному запросу ничего'
                                  ' не найдено. '
                                  'Попробуйте использовать более общий запрос.')
        if len(result['items']) < 1:
            return await ctx.send('По данному запросу ничего не найдено. '
                                  'Попробуйте использовать более общий запрос.')
        random_number = random.randint(0, len(result['items'])-1)
        await ctx.send(urllib.parse.unquote(result['items'][random_number]['link']))
        await ctx.send("Картинка по запросу: \"" + message + "\"")


@commands.command(pass_context=True)
async def g(ctx, *, query):
    """Google web search. Ex: [p]g what is discordapp?"""
    await ctx.message.delete()
    async with aiohttp.ClientSession() as session:
        if query[-1].isdigit():
            i = int(query[0])
            query = query[:-1].strip()
        else:
            i = 0
        resp = await session.get(
                            "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(query) +
                            "&start=1" + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID)
        result = json.loads(await resp.text())
        if not i:
            await ctx.send(urllib.parse.unquote(result['items'][i]['link']))
            await ctx.send("Ссылка по запросу: \"" + query + "\"")
        else:
            info = discord.Embed(title=f'Ссылки по запросу {query}', color=discord.Color.green())
            for k in range(i):
                info.add_field(name=str(k+1), value=urllib.parse.unquote(result['items'][k]['link']), inline=False)
            await ctx.send(embed=info)

