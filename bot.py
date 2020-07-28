import asyncio
import re
import random
import time
import psycopg2
import discord
import types


from discord.ext import commands
from configuration import *
import google_search
import logs

MESSAGES, SYMBOLS = 0, 0
AUTHORS = {}

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
    print('Bot connected')


@client.event
async def on_command_error(ctx, error):
    await ctx.message.delete()
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(f'{ctx.message.author.name} погоди мой сладкий я почилю еще %.2f cек и тогда сделаю'
                       f'все что смогу для тебя' % error.retry_after)
    elif isinstance(error, discord.ext.commands.errors.CommandNotFound):
        await ctx.send(f'Команда {ctx.message.content} не была обноружена')
    raise error  # re-raise the error so all the errors will still show up in console


@client.event
async def on_message(message):
    await client.process_commands(message)
    msg = message.content.lower()
    global AUTHORS, MESSAGES, SYMBOLS
    if message.author.id != 698973448772386927:
        MESSAGES += 1
        SYMBOLS += len(msg.replace(' ', ''))

        AUTHORS[message.author.id] = [i + x for i, x in zip([1, len(msg.replace(' ', ''))],
                                                            AUTHORS.get(message.author.id, [0, 0]))]
    msg_check = re.search(
        r'[\w\s]*[rр]+\s*[aа]+\s*[nн]+[\s*гrg]+\s*[aаeе]+[\s\w]*([лl]+\s*[0oо]+\s*(?:[hxхз]+|'
        r'(?:}{)+)|(?:]\[)+)[\w\s]*', msg)
    if msg_check:
        await message.delete()
        await message.channel.send(f'{message.author.name} слышь чорт, сам ты {msg_check[1]}')
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
    channel = client.get_channel(698975367326728352)  #698975228323168271
    while not client.is_closed():
        conn, cur = db()
        if MESSAGES:
            await logs.send_data_for_day(channel, AUTHORS, MESSAGES, SYMBOLS)
            logs.update_stats_author_day(conn, cur, AUTHORS)
            logs.update_stats_max_day(cur, MESSAGES, SYMBOLS)
        await logs.send_data_schedule(cur, channel)
        logs.update_stats_schedule(cur)
        logs.update_stats_max_month(cur)
        conn.commit()
        conn.close()

        SYMBOLS, MESSAGES, AUTHORS = 0, 0, {}
        next_day = abs(3600*24 - sum([i * x for i, x in zip(map(lambda i: time.localtime()[i],
                                                            range(3, 6)), [3600, 60, 1])])-3600)
        print(next_day)
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
        info_dict = logs.channel_data(cur)
        for k, v in {k: v for k, v in info_dict.items() if v}.items():
            if hasattr(k, '__call__'):
                k = k()
            if hasattr(v, '__call__'):
                v = v()
            info.add_field(name=k, value=v, inline=False)
        await ctx.send(embed=info)
    else:
        info = discord.Embed(title=f'Статистика по запросу пользователю',
                             color=discord.Color.green())
        info.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        info_dict = logs.author_data(ctx, cur, AUTHORS)
        for k, v in {k: v for k, v in info_dict.items() if v}.items():
            if hasattr(k, '__call__'):
                k = k()
            if hasattr(v, '__call__'):
                v = v()
            info.add_field(name=k, value=v, inline=False)
        await ctx.send(embed=info)
    conn.close()


@client.command(pass_context = True)
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
    emb = discord.Embed(title='Навигация по командам', colour=discord.Color.blue())
    emb.set_image(url=r'https://i.gifer.com/origin/6b/6bd46e83cec1fc9390a64e9ae7e085f2_w200.gif')
    emb.add_field(name=f'{PREFIX}clear N', value='удаление N сообщений из чата (по умолчанию 10)')
    emb.add_field(name=f'{PREFIX}unban member', value='разбанить пользователя member'
                                                      '(указать ник и id --> ник#id)')
    emb.add_field(name=f'{PREFIX}ban member reason',
                  value='забанить пользователя member (указать ник) и причину reason')
    emb.add_field(name=f'{PREFIX}kick member', value='кикнуть пользователя member (указать ник)')
    emb.add_field(name=f'{PREFIX}hello фраза', value='поприветсвовать (необязательный аргумент фраза)')
    emb.add_field(name=f'{PREFIX}mute member N', value='Замутить пользователя member '
                                                       'на N - часов (по умолчанию N=1)')
    emb.add_field(name=f'{PREFIX}unmute member', value='Размутить пользователя member')
    emb.add_field(name=f'{PREFIX}i query', value='Искать картинку с названием query')
    emb.add_field(name=f'{PREFIX}g query', value='Сделать поисковый запрос с текстом query')
    emb.add_field(name=f'{PREFIX}stats (additional info)',
                  value='Показать статистику сообщений \n '
                        'Additional info -- month (max, peak)\n'
                        'day (max, peak); week')
    emb.add_field(name=f'{PREFIX}cit', value='Случайная цитата из списка внесенных')
    emb.add_field(name=f'{PREFIX}dob', value='Добавить цитату. По умолчанию автор сообщения - автор цитаты. '
                                             'Что-бы укзаать другого автора, добавить в первом слове двоеточие '
                                             'Имя_Фамилия: Текст: Цитата автора')
    await ctx.send(embed=emb)


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
