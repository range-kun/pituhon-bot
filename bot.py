import asyncio
import itertools
import random
import re
import urllib.parse

import aiohttp
import aioschedule as schedule
import discord
import yaml
from bs4 import BeautifulSoup
from discord.ext import commands

from cogs.google_search import Google
from cogs.message_stats import MessageStats
from cogs.poll import Poll, PollMessageTrack
from cogs.translate import Translate
from cogs.voice_message import VoiceMessage
from configuration import TOKEN, UMBRA_ID, MAIN_CHANNEL_ID
from utils import today, send_yaml_text
from utils.data.history_record import HistoryRecord
from utils.data.phrase import PhraseData
from utils.message_stats_routine import MessageDayCounter as MDC
from utils.message_stats_routine.chanel_stats_routine import ChanelStats
from utils.message_stats_routine.user_stats_routine import UserStats

CAPS = 0
NAHOOJ = 0
PREFIX = '?'  # command_prefix

HELLO_WORDS = ['ky', 'ку']
ANSWER_WORDS = ['узнать информацию о себе', 'какая информация',
                'команды', 'команды сервера', 'что здесь делать']
GOODBYE_WORDS = ['бб', 'bb', 'лан я пошел', 'я спать']

intents = discord.Intents().default()
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
bot.remove_command('help')


@bot.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(f'{ctx.message.author.name} погоди мой сладкий я почилю еще %.2f cек и тогда сделаю'
                       f' все что смогу для тебя' % error.retry_after)
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(f'Команда {ctx.message.content} не была обноружена')
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send(f'Команде {ctx.message.content} не хватает аргументов, '
                       f'наберите ?cmds для подсказки')
    raise error  # re-raise the error so all the errors will still show up in console


@bot.event
async def on_message(message):
    print()
    MDC.proceed_message_info(message)
    msg_text = message.content.lower()

    nahoj_messages = [
        "Нахуй иди",
        "Съебался",
        f"Выполняю обработку команды {msg_text}, а нет не выполняю, иди нахуй, черт",
        "У меня перерыв 15 минут прошу простить",
        "Докажите что вы человек чтобы воспользоватья ботом",
        msg_text * 3
    ]
    if NAHOOJ and message.author.id == UMBRA_ID and message.channel.id == MAIN_CHANNEL_ID:
        if msg_text.startswith(PREFIX):
            nahooj_message = random.choice(nahoj_messages)
            await message.channel.send(nahooj_message)
            return

    await bot.process_commands(message)

    url_check = re.search(r'^(?:https?:\/\/)?(?:w{3}\.)?', msg_text)
    if url_check and message.content != urllib.parse.unquote(message.content):
        await message.delete()
        message.content = urllib.parse.unquote(message.content)
        await message.channel.send(f'<@{message.author.id}>: {message.content}')

    range_lox_regex = re.search(
        r'[\w\s]*[rр]+\s*[aа]+\s*[nн]+[\s*гrg]+\s*[aаeе]+[\s\w]*([лl]+\s*[0oо]+\s*(?:[hxхз]+|'
        r'(?:}{)+)|(?:]\[)+)[\w\s]*', msg_text)
    if range_lox_regex:
        swear_word = range_lox_regex[1]
        await message.delete()
        await message.channel.send(f'{message.author.name} слышь чорт, сам ты {swear_word}')

    if any(i.isalpha() for i in msg_text) and message.content.upper() == message.content and CAPS:
        await message.delete()
        await message.channel.send(f'{message.author.name}: {message.content.capitalize()}')
    if msg_text in HELLO_WORDS:
        await message.channel.send('Привет, чо надо, идите нахуй я вас не знаю')
    elif msg_text in ANSWER_WORDS:
        await message.channel.send(f'напиши {PREFIX}cmds и тебе откроются все тайны')
    elif msg_text in GOODBYE_WORDS:
        await message.channel.send('{} пиздуй бороздуй и я попиздил'.format(message.author.name))


@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if reaction.message.id in PollMessageTrack.poll_user_stats:
        await PollMessageTrack.save_or_update_reactions(reaction, user)


@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id not in PollMessageTrack.poll_user_stats:
        return
    await PollMessageTrack.process_removal_of_reaction(payload.message_id, payload.user_id)


# get random phrase
@bot.command(pass_context=True)
async def cit(ctx):
    author, text = PhraseData.get_random_phrase()
    await ctx.send(f"{author}: {text}")


# add phrase
@bot.command(pass_context=True)
async def dob(ctx, *text):
    if text[0].endswith(':'):
        author = text[0].replace('_', ' ').rstrip(':').title()
        text = text[1:]
    else:
        author = ctx.author.name
    text = ' '.join(text)

    PhraseData.insert(
        author=author,
        text=text
    )
    await ctx.send('Было добавлено фраза: '+author+': '+text)


# add history log
@bot.command(pass_context=True)
async def hist(ctx, *, text: str):
    HistoryRecord.insert(date=today(), log=text.capitalize())
    await ctx.send(f'{today().strftime("%d-%m-%Y")} - было добавлено воспоминание: {text}')


@bot.command(pass_context=True)
async def rec(ctx, text=None, *, num=None):
    result = HistoryRecord.get_record(text, offset=num)
    if type(result) == str:
        await ctx.send(result)
        return
    output = ""
    for date, record in result:
        date_for_output = date.strftime("%d-%m-%Y")
        output += f"{date_for_output}: {record}\n"
    await ctx.send(output)


# forbid to use CAPSLOCK
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def caps(ctx):
    global CAPS
    CAPS = 0 if CAPS else 1
    caps_info = {0: 'Caps allowed', 1: 'Caps not allowed'}
    await ctx.send(caps_info[CAPS])


@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def nah(ctx):
    global NAHOOJ
    NAHOOJ = 0 if NAHOOJ else 1
    nahhoj_info = {0: "Ne nahooj", 1: "Nahooy"}
    await ctx.send(nahhoj_info[NAHOOJ])


# clear
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=10):
    await ctx.channel.purge(limit=amount+1)


# kick
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await ctx.message.delete()
    await member.kick(reason=reason)
    await ctx.send('Выгнали {} на мороз'.format(member.mention))


# ban
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason):
    await ctx.message.delete()
    await member.ban(reason=reason)
    await ctx.send('Такие как {} нам явно не нужны'.format(member.mention))


# unban
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def unban(ctx, *, member):
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')
    info = [(ban_entry.user.name, ban_entry.user.discriminator) for ban_entry in banned_users]
    if (member_name, member_discriminator) in info:
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send('Разбанен {}'.format(user))
                return
    else:
        await ctx.send('Пользователь {} не найден в списке забаненых'.format(member))


# help
@bot.command(pass_context=True)
async def cmds(ctx):
    output = ""
    await ctx.send('**Список доступных комманд**')
    try:
        with open('commands_description.yaml', encoding="utf-8") as file:
            commands_description = yaml.safe_load(file)["commands_description"]
    except FileNotFoundError:
        await ctx.send(r'При попытки вызвать команду cmds произошла ошибка на стороне сервера, ¯\_(ツ)_/¯')
        return

    for command_name, description in commands_description.items():
        output += f"{PREFIX}{command_name}".ljust(20) + f"-- {description} \n"
        if command_name == "hist text":  # because description above 2000 symbols and bot won't send it
            await send_yaml_text(output, ctx)
            output = ""
    await send_yaml_text(output, ctx)

    languages_info = discord.Embed(
        title='Список языков и их сокращения',
        url='https://gist.githubusercontent.com/astronautlevel2/'
            '93a19379bd52b351dbc6eef269efa0bc/raw/18d55123bc85e2ef8f54e09007489ceff9b3ba51/langs.json')
    await ctx.send(embed=languages_info)


# mute
@bot.command
@commands.has_permissions(administrator=True)
async def mute(ctx, member: discord.Member, duration: int = 1):
    mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
    if mute_role in member.roles:
        await ctx.send(f"{member} уже замучен")
        return
    else:
        tail = '{} час'.format(duration) + 'a' * \
               (1 < duration % 10 < 5 and duration not in range(5, 21)) + \
               'ов' * (4 < duration % 10 < 9 or duration in range(5, 21) or duration % 10 == 0)
        await member.add_roles(mute_role)
        overwrite = discord.PermissionOverwrite(send_messages=False)
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(mute_role, overwrite=overwrite)
        await ctx.send('{} был замьючен на '.format(member.mention) + tail)
        await asyncio.sleep(duration * 3600)
        await member.remove_roles(mute_role)
        return


# unmute
@bot.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member: discord.Member):
    mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
    if mute_role not in member.roles:
        await ctx.send(f"{member} не замучен")
        return
    else:
        await member.remove_roles(mute_role)
        await ctx.send('{} отмьючен'.format(member.mention))
        return


@bot.command()
async def f(ctx):
    member_name = ctx.author.name

    async with aiohttp.ClientSession() as session:
        resp = await session.get('https://randstuff.ru/fact/')
    if resp.status != 200:
        await ctx.send('Ошибка на стороне сервера повторите попытку позже')
        return

    text = await resp.text()
    soup = BeautifulSoup(text, "lxml")
    fact = soup.find("table", class_="text").find('td').text
    return await ctx.send(f"Интересный факт для {member_name}: \n{fact}")


schedule.every().day.at("23:00").do(UserStats.daily_routine)
schedule.every().sunday.at("23:03").do(UserStats.weekly_routine)
schedule.every().day.at("23:06").do(UserStats.monthly_routine)

schedule.every().day.at("23:10").do(ChanelStats.daily_routine)
schedule.every().sunday.at("23:13").do(ChanelStats.weekly_routine)
schedule.every().day.at("23:16").do(ChanelStats.monthly_routine)


schedule.every().day.at("23:20").do(MDC.delete_redis_info)
schedule.every(20).minutes.do(MDC.counter_routine)


async def my_schedule():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(5)


@bot.event
async def on_ready():
    ChanelStats.set_bot(bot)
    bot.loop.create_task(my_schedule())
    bot.add_cog(Google(bot))
    bot.add_cog(Translate(bot))
    bot.add_cog(MessageStats(bot))
    bot.add_cog(Poll(bot))
    bot.add_cog(VoiceMessage(bot))
    print('Bot connected')

bot.run(TOKEN)
