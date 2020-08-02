import aiohttp
import urllib.parse
import re
import random
import json

from discord.ext import commands
from configuration import API_KEY, SEARCH_ENGINE_ID


@commands.cooldown(1, 30, commands.BucketType.user)
@commands.command(pass_context=True, aliases=['image', 'img'])
async def i(ctx, *, message):       #get random phto from google
    await ctx.message.delete()
    if ctx.channel.id != 734684085569454111:
        msg_check = re.search(r'[\w\s]*(?:(?:[тt]+[rр]+[аa]+[нn]+[сc]+[ыe]+)|'
                              r'(?:(?:(?:баб[ыа])|(?:тян)|(?:женщина[ыа])|(?:девушк[иа])) с '
                              r'(?:(?:ху[яе]ми*)|(?:членом)|(?:письк(?:(?:ой)|(?:ами)))))'
                              r'|(?:трасвиститы*))[\w\s]*', message, re.I)
        if msg_check:
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
        except:
            return await ctx.send('По данному запросу ничего'
                                  ' не найдено. '
                                  'Попробуйте использовать более общий запрос.')
        if len(result['items']) < 1:
            return await ctx.send('По данному запросу ничего не найдено. '
                                  'Попробуйте использовать более общий запрос.')
        i = random.randint(0, len(result['items'])-1)
        await ctx.send(result['items'][i]['link'])
        await ctx.send("Картинка по запросу: \"" + message + "\"")


@commands.command(pass_context=True)
async def g(ctx, *, query):
    """Google web search. Ex: [p]g what is discordapp?"""
    await ctx.message.delete()
    async with aiohttp.ClientSession() as session:
        if query[0].isdigit():
            i = int(query[0])
            query = query[1:]
        else:
            i = 0
        resp = await session.get(
                            "https://www.googleapis.com/customsearch/v1?q=" + urllib.parse.quote_plus(query) +
                            "&start=1" + "&key=" + API_KEY + "&cx=" + SEARCH_ENGINE_ID)
        result = json.loads(await resp.text())
        await ctx.send(urllib.parse.unquote(result['items'][i]['link']))
        await ctx.send("Ссылка по запросу: \"" + query + "\"")

