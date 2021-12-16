import asyncio
import itertools
import re
import urllib.parse

import discord
from discord.ext import commands
import psycopg2
import aioschedule as schedule
import yaml

from configuration import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, TOKEN
from utils.data.phrase import PhraseData
from utils.data.history_record import HistoryRecord
from cogs.google_search import Google
from cogs.translate import Translate
from utils import today
from utils.message_stats import MessageCounter as MC
from utils.message_stats.user_stats import UserStats
from utils.message_stats.chanel_stats import ChanelStats
import logs


CAPS_INFO = itertools.cycle({0: 'Caps allowed', 1: 'Caps not allowed'})

# command_prefix
CAPS = 0
PREFIX = '?'

bot = commands.Bot(command_prefix=PREFIX)
bot.remove_command('help')

HELLO_WORDS = ['ky', 'ку']
ANSWER_WORDS = ['узнать информацию о себе', 'какая информация',
                'команды', 'команды сервера', 'что здесь делать']
GOODBYE_WORDS = ['бб', 'bb', 'лан я пошел', 'я спать']


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
    await bot.process_commands(message)
    MC.proceed_message_info(message)
    msg_text = message.content.lower()

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


# data base connection
def db():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASSWORD,
                            host=DB_HOST, port='5432'
                            )
    cur = conn.cursor()
    return conn, cur


@bot.command(pass_context=True)
async def stats(ctx, *, text=None):
    if text:
        text = text.lower()
    conn, cur = db()
    if text == 'ch':
        info = discord.Embed(title=f'Статистика по серверу {ctx.message.guild.name}',
                             color=discord.Color.green())
        info.set_image(url=ctx.guild.icon_url)
        return await logs.final_stats(info, ctx, logs.channel_data, cur)
    elif text == 'day':
        await logs.author_data_for_period(ctx, cur, MC.authors, 'За сегодня:')
    elif text == 'week':
        await logs.author_data_for_period(ctx, cur, MC.authors, 'За неделю:')
    elif text == 'month':
        await logs.author_data_for_period(ctx, cur, MC.authors, 'За месяц:')
    elif text == 'max':
        await logs.author_data_for_period(ctx, cur, MC.authors,
                                          'Максимальные показатели', 'За день', 'За месяц')
    else:
        info = discord.Embed(title=f'Статистика по запросу пользователю',
                             color=discord.Color.green())
        info.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await logs.final_stats(info, ctx, logs.author_data, cur, MC.authors)
    conn.close()
    return


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
async def rec(ctx, text, *, num=None):
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
async def caps(ctx):
    global CAPS
    CAPS = 0 if CAPS else 1
    caps_info = {0: 'Caps allowed', 1: 'Caps not allowed'}
    await ctx.send(caps_info[CAPS])


# clear
@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=10):
    await ctx.channel.purge(limit=amount)


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
    yaml_message_style = str(f"```yaml\n{output}```")
    await ctx.send(yaml_message_style)
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

schedule.every().day.at("23:40").do(UserStats.daily_routine)
schedule.every().thursday.at("23:16").do(UserStats.weekly_routine)
schedule.every().day.at("23:44").do(UserStats.monthly_routine)

schedule.every().day.at("23:50").do(ChanelStats.daily_routine)
schedule.every().monday.at("23:52").do(ChanelStats.weekly_routine)
schedule.every().day.at("23:54").do(ChanelStats.monthly_routine)

schedule.every().day.at("23:56").do(MC.set_stats_to_zero)


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
    print('Bot connected')

bot.run(TOKEN)
