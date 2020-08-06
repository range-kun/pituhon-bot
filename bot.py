import asyncio
import re
import random
import time
import psycopg2
import discord
import itertools
import urllib.parse
import google_search
import translate

from discord.ext import commands
from configuration import *
import logs

MESSAGES, SYMBOLS = 0, 0
AUTHORS = {}
CAPS = 0
CAPS_INFO = itertools.cycle({0: 'Caps allowed', 1: 'Caps not allowed'})

PREFIX = '?'

client = commands.Bot(command_prefix=PREFIX)
client.remove_command('help')

# command_prefix какие префиксы должны использоваться перед командой

hello_words = ['ky', 'ку']
answer_words = ['узнать информацию о себе', 'какая информация',
                'команды', 'команды сервера', 'что здесь делать']
goodbye_words = ['бб', 'bb', 'лан я пошел']


@client.event
async def on_ready():
    client.add_command(google_search.i)
    client.add_command(google_search.g)
    client.add_command(translate.trans)
    print('Bot connected')


@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(f'{ctx.message.author.name} погоди мой сладкий я почилю еще %.2f cек и тогда сделаю '
                       f'все что смогу для тебя' % error.retry_after)
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(f'Команда {ctx.message.content} не была обноружена')
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send(f'Команде {ctx.message.content} не хватает аргументов')
    raise error  # re-raise the error so all the errors will still show up in console


@client.event
async def on_message(message):
    await client.process_commands(message)
    msg = message.content.lower()
    global AUTHORS, MESSAGES, SYMBOLS
    if message.author.id != 698973448772386927:
        MESSAGES += 1
        if re.search(r'<:\w+:\d+>', msg):
            temp_symb = 1
            SYMBOLS += 1
        else:
            temp_symb = len(msg.replace(' ', ''))
            SYMBOLS += len(msg.replace(' ', ''))
        AUTHORS[message.author.id] = [i + x for i, x in zip([1, temp_symb],
                                                            AUTHORS.get(message.author.id, [0, 0]))]
    url_check = re.search('^(?:https?:\/\/)?(?:w{3}\.)?', msg)
    range_check = re.search(
        r'[\w\s]*[rр]+\s*[aа]+\s*[nн]+[\s*гrg]+\s*[aаeе]+[\s\w]*([лl]+\s*[0oо]+\s*(?:[hxхз]+|'
        r'(?:}{)+)|(?:]\[)+)[\w\s]*', msg)
    if url_check and message.content != urllib.parse.unquote(message.content):
        await message.delete()
        message.content = urllib.parse.unquote(message.content)
        await message.channel.send(f'<@{message.author.id}>: {message.content}')
    if range_check:
        await message.delete()
        await message.channel.send(f'{message.author.name} слышь чорт, сам ты {range_check[1]}')
    if any(i.isalpha() for i in msg) and message.content.upper() == message.content and CAPS:
        await message.delete()
        await message.channel.send(f'{message.author.name}: {message.content.capitalize()}')
    if msg in hello_words:
        await message.channel.send('Привет, чо надо, идите нахуй я вас не знаю')
    elif msg in answer_words:
        await message.channel.send('напиши help и тебе откроются все тайны')
    elif msg in goodbye_words:
        await message.channel.send('{} пиздуй бороздуй и я попиздил'.format(message.author.name))


#data base connection
def db():
    conn = psycopg2.connect(dbname='d3lg89is3baabv', user=DB_USER,
                            password=DB_PASSWORD,
                            host='ec2-54-75-229-28.eu-west-1.compute.amazonaws.com', port='5432')
    cur = conn.cursor()
    return conn, cur


# log data
async def log():
    await client.wait_until_ready()
    global MESSAGES, SYMBOLS, AUTHORS
    channel = client.get_channel(698975367326728352)  #test mode
    #channel = client.get_channel(698975228323168271)    #run mode
    while not client.is_closed():
        conn, cur = db()
        if MESSAGES:
            await logs.send_data_for_day(channel, AUTHORS, MESSAGES, SYMBOLS, client)
            logs.update_stats_author_day(conn, cur, AUTHORS, MESSAGES, SYMBOLS)
        await logs.send_data_schedule(cur, channel, client)
        logs.update_stats_schedule(cur)
        conn.commit()
        conn.close()

        SYMBOLS, MESSAGES, AUTHORS = 0, 0, {}
        next_day = 3600*24 - sum([i * x for i, x in zip(map(lambda i: time.localtime()[i],
                                                            range(3, 6)), [3600, 60, 1])])
        await asyncio.sleep(next_day)


@client.command(pass_context=True)
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
        await logs.author_data_for_period(ctx, cur, AUTHORS, 'За сегодня:')
    elif text == 'week':
        await logs.author_data_for_period(ctx, cur, AUTHORS, 'За неделю:')
    elif text == 'month':
        await logs.author_data_for_period(ctx, cur, AUTHORS, 'За месяц:')
    elif text == 'max':
        await logs.author_data_for_period(ctx, cur, AUTHORS,
                                          'Максимальные показатели', 'За день', 'За месяц')
    else:
        info = discord.Embed(title=f'Статистика по запросу пользователю',
                             color=discord.Color.green())
        info.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        await logs.final_stats(info, ctx, logs.author_data, cur, AUTHORS)
    conn.close()
    return


@client.command(pass_context=True)
async def cit(ctx):
    conn, cur = db()
    cur.execute("SELECT AUTHOR, FRAZA  from phraces")
    with conn:
        rows = [' '.join(i) for i in cur.fetchall()]
    await ctx.send(random.choice(rows))


# add pharace
@client.command(pass_context=True)
async def dob(ctx, *text):
    if text[0].endswith(':'):
        author = text[0].replace('_', ' ').rstrip(':').title()
        text = text[1:]
    else:
        author = ctx.author.name
    text = ' '.join(text)
    conn, cursor = db()
    with conn:
        cursor.execute(f"INSERT INTO PHRACES (AUTHOR,FRAZA) \
                        VALUES ('{author}:','{text}')")
        conn.commit()
        await ctx.send('Была добавлена фраза: '+author+': '+text)


# add hitory log
@client.command(pass_context=True)
async def hist(ctx, *, text):
    conn, cur = db()
    date_check = re.match(r'(\d{2}-\d{2}-\d{4})', text)
    if date_check:
        date = '-'.join(date_check[1].split('-')[::-1])
        cur.execute(f"SELECT log from history_logs where date='{date}'")
        history_log = cur.fetchall()
        if history_log:
            await ctx.send(f'Воспоминания за {date_check[1]}:')
            for log in history_log:
                await ctx.send(f'{log[0]}')
        else:
            await ctx.send('На указанную дату логов не найдено')
    else:
        cur.execute(f"INSERT INTO history_logs (date, log) values ('{logs.today()}', '{text.capitalize()}')")
        await ctx.send(f'{logs.today().strftime("%d-%m-%Y")} - была добавлена фраза: {text}')
        conn.commit()


@client.command(pass_context=True)
async def caps(ctx):
    global CAPS
    CAPS = 0 if CAPS else 1
    caps_info = {0: 'Caps allowed', 1: 'Caps not allowed'}
    await ctx.send(caps_info[CAPS])


# clear
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx, amount=10):
    await ctx.channel.purge(limit=amount)


# kick
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await ctx.message.delete()
    await member.kick(reason=reason)
    await ctx.send('Выгнали {} на мороз'.format(member.mention))


# ban
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def ban(ctx, member: discord.Member, *, reason):
    await ctx.message.delete()
    await member.ban(reason=reason)
    await ctx.send('Такие как {} нам явно не нужны'.format(member.mention))


# unban

@client.command(pass_context=True)
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


@client.command(pass_context=True)
async def hello(ctx, arg=None):
    author = ctx.message.author
    if arg:
        await ctx.send(f"Hello {author.name}")
    else:
        await ctx.send(f"Hello {author.name} {arg}")


# help
@client.command(pass_context=True)
async def help(ctx):
    await ctx.send('**Навигация по командам**')
    message = f'{PREFIX}clear N'.ljust(20) + '-- удаление N сообщений из чата (по умолчанию 10)\n' + \
              f'{PREFIX}ban member reason'.ljust(20) +'-- забанить пользователя member ' \
              f'(@упомянуть) указать причину reason\n' + \
              f'{PREFIX}unban member'.ljust(20) + '-- разбанить пользователя member' +\
              f'(указать ник и id -> ник#id)\n' + \
              f'{PREFIX}kick member'.ljust(20) + '-- кикнуть пользователя member (@упомянуть)\n' + \
              f'{PREFIX}mute member N'.ljust(20) + '-- замутить пользователя @member '  + \
              'на N - часов (по умолчанию на час )\n' + \
              f'{PREFIX}unmute member'.ljust(20) + '-- размутить пользователя member\n' + \
              f'{PREFIX}caps'.ljust(20) + '-- разрешить/запретить CapsLock \n' + \
              f'{PREFIX}hello фраза'.ljust(20) + '-- поздоровайтесь с ботом (необязательный аргумент фраза) \n' + \
              f'{PREFIX}i query'.ljust(20) + '-- искать картинку с названием query \n' + \
              f'{PREFIX}g query'.ljust(20) + '-- сделать поисковый запрос в google с текстом query \n' + \
              f'если в конце указать цифру n (небольше 10) выдаст первые n запросов\n' + \
              f'{PREFIX}cit'.ljust(20) + '-- случайная цитата из списка внесенных \n' + \
              f'{PREFIX}dob'.ljust(20) + '-- добавить цитату. По умолчанию автор сообщения - автор цитаты. \n' + \
              'Что-бы укзаать другого автора, добавить в первом слове двоеточие: ' \
              'Имя_Фамилия: Текст \n' + \
              f'{PREFIX}stats (доп параметры: day, week, month, max) -- показать статистику пользователя \n' + \
              f'{PREFIX}stats ch'.ljust(20) + '-- показать статистику канала \n' + \
              f'{PREFIX}hist дата'.ljust(20) + '-- искать воспоминания за указанную дату (формат даты дд-мм-гггг) \n' + \
              f'{PREFIX}hist текст'.ljust(20) + '-- добавить записть в воспоминания за сегодняшнее число \n' + \
              f'{PREFIX}translate Язык текст -- перевести текст на указанный язык'
    retStr = str(f"```yaml\n{message}```")
    await ctx.send(retStr)
    languages_info = discord.Embed(title='Список языков и их сокращения',
                                   url='https://gist.githubusercontent.com/astronautlevel2/93a19379bd52b351'
                                       'dbc6eef269efa0bc/raw/18d55123bc85e2ef8f54e09007489ceff9b3ba51/langs.json')
    await ctx.send(embed=languages_info)

# mute
@client.command()
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
@client.command()
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
# connect
client.loop.create_task(log())
client.run(TOKEN)
