import asyncio
import re
import random

import discord
import psycopg2
from discord.ext import commands
from configuration import *
import google_search

PREFIX='?'


client=commands.Bot(command_prefix=PREFIX)
client.remove_command('help')
#command_prefi какие префиксы должны использоваться перед командой

hello_words=['ky','ку']
answer_words=['узнать информацию о себе', 'какая информация','команды','команды сервера','что здесь делать']
goodbye_words=['бб','bb','лан я пошел']

def db():
    conn = psycopg2.connect(dbname='d3lg89is3baabv', user=DB_USER,
                            password=DB_PASSWORD,
                            host='ec2-54-75-229-28.eu-west-1.compute.amazonaws.com', port='5432')

    cur = conn.cursor()
    return conn, cur

@client.event
async def on_ready():
    client.add_command(google_search.i)
    client.add_command(google_search.g)
    print('Bot connected')

@client.event
async def on_command_error(ctx,error):
    await ctx.message.delete()
    if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(f'{ctx.message.author.name} погоди мой сладкий я почилю еще %.2fcек и тогда сделаю'
                       f'все что смогу для тебя' % error.retry_after)
    raise error  # re-raise the error so all the errors will still show up in console

@client.event
async def on_message(message):
    await client.process_commands(message)
    msg=message.content.lower()
    msg_check=re.search(r'[\w\s]*[rр]+\s*[aа]+\s*[nн]+[\s*гrg]+\s*[aаeе]+[\s\w]*([лl]+\s*[0oо]+\s*(?:[hxхз]+|(?:}{)+)|(?:]\[)+)[\w\s]*',msg)
    if msg_check:
        await message.delete()
        await message.channel.send(f'{message.author.name} слышь чорт, сам ты {msg_check[1]}')
    if msg in hello_words:
        await message.channel.send('Привет, чо надо, идите нахуй я вас не знаю')
    elif msg in answer_words:
        await message.channel.send('напиши help и тебе откроются все тайны')
    elif msg in goodbye_words:
        await message.channel.send('{} пиздуй бороздуй и я попиздил'.format(message.author.name))

@client.command(pass_context=True)
async def mudrost(ctx):
    conn, cur = db()
    cur.execute("SELECT AUThor, FRAZA  from phraces")
    with conn:
        rows = [' '.join(i) for i in cur.fetchall()]
    await ctx.send(random.choice(rows))
@client.command(pass_context=True)
async def dob(ctx,*text):
    if text[-1].endswith('---'):
        author=text[-1].rstrip('-').capitalize()
        text=text[:-1]
    else:
        author=ctx.author.name
    text=' '.join(text)
    conn, cursor = db()
    with conn:
        cursor.execute(f"INSERT INTO PHRACES (AUTHOR,FRAZA) \
                        VALUES ('{author}:','{text}')");
        conn.commit()


#clear
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def clear(ctx,amount=10):
    await ctx.channel.purge(limit=amount)

#kick
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def kick(ctx,member:discord.Member, *,reason=None):
    await ctx.message.delete()
    await member.kick(reason=reason)
    await ctx.send('Выгнали {} на мороз'.format(member.mention))

#ban
@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def ban(ctx,member:discord.Member,*,reason):
    await ctx.message.delete()
    await member.ban(reason=reason)
    await ctx.send('Такие как {} нам явно не нужны'.format(member.mention))

#unban

@client.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def unban(ctx,*,member):
    banned_users=await ctx.guild.bans()
    member_name, member_discriminator=member.split('#')
    info=[(ban_entry.user.name, ban_entry.user.discriminator) for ban_entry in banned_users]
    if (member_name, member_discriminator)  in info:
        for ban_entry in banned_users:
            user=ban_entry.user
            if (user.name, user.discriminator)==(member_name,member_discriminator):
                  await ctx.guild.unban(user)
                  await ctx.send('Разбанен {}'.format(user))
                  return
    else:
        await ctx.send('Пользователь {} не найден в списке забаненых'.format(member))


@client.command(pass_context=True)
async def hello (ctx, arg=None):
    author=ctx.message.author
    if arg==None: await ctx.send (f"Hello {author.name}")
    else : await ctx.send (f"Hello {author.name} {arg}")
#help
@client.command(pass_context=True)
async def help (ctx):
    emb=discord.Embed(title='Навигация по командам')

    emb.add_field(name=f'{PREFIX}clear N', value='удаление N сообщений из чата (по умолчанию 10)')
    emb.add_field(name=f'{PREFIX}unban member', value='разбанить пользователя member (указать ник и id --> ник#id)')
    emb.add_field(name=f'{PREFIX}ban member reason',
                  value='забанить пользователя member (указать ник) и причину reason')
    emb.add_field(name=f'{PREFIX}kick member', value='кикнуть пользователя member (указать ник)')
    emb.add_field(name=f'{PREFIX}hello фраза', value='поприветсвовать (необязательный аргумент фраза)')
    emb.add_field(name=f'{PREFIX}mute member N', value='Замутить пользователя member на N - часов (по умолчанию N=1)')
    emb.add_field(name=f'{PREFIX}unmute member', value='Размутить пользователя member')
    emb.add_field(name=f'{PREFIX}i query', value='Искать картинку с названием query')

    await ctx.send(embed=emb)

#mute
@client.command()
@commands.has_permissions(administrator=True)
async def mute(ctx, member:discord.Member,duration:int=1):
    mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
    if mute_role in member.roles:
        await ctx.send(f"{member} уже замучен")
        return
    else:
        tail= '{} час'.format(duration)+'a'*(1<duration%10<5 and duration not in range(5,21)) +\
              'ов'*(4<duration%10<9 or duration in range (5,21) or duration%10==0)
        await member.add_roles(mute_role)
        overwrite=discord.PermissionOverwrite(send_messages=False)
        for channel in ctx.guild.text_channels:
            await channel.set_permissions(mute_role, overwrite=overwrite)
        await ctx.send('{} был замьючен на '.format(member.mention)+tail)
        await asyncio.sleep(1*3600)
        await member.remove_roles(mute_role)
        return

#unmute
@client.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member:discord.Member):
    mute_role = discord.utils.get(ctx.message.guild.roles, name='mute')
    if mute_role not in member.roles:
        await ctx.send(f"{member} не замучен")
        return
    else:
        await member.remove_roles(mute_role)
        await ctx.send('{} отмьючен'.format(member.mention))
        return

#connect

client.run(TOKEN)

