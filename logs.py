import time
from datetime import datetime, timedelta
import discord

from utils.message_stats import MessageCounter as MC

#########stats command############

def send_channel_peak(cur, period, date_format=None,):
    cur.execute(f"SELECT messages, symbols, date_peak_messages, date_peak_symbols"
                f" FROM ACTIVITY WHERE PERIOD='{period}'")
    row = list(cur.fetchone())
    return final_message(row, date_format, edit=True)


def send_data_author_current(cur, ctx, table, id_num, today_data):
    cur.execute(f'SELECT MESSAGES,SYMBOLS FROM {table} where {id_num}={ctx.author.id}')
    row = cur.fetchone()
    if not row:
        return None
    else:
        return f'Кол-во сообщений  =>{row[0]+today_data[0]}.\nКол-во символов  =>{row[1]+today_data[1]}'


def send_data_author_max(cur, ctx, table, date_format=None, message=None):
    cur.execute(f"SELECT messages, symbols, top_messages_date, top_symbols_date"
                f" from {table} where author_id={ctx.author.id}")
    row = list(cur.fetchone())
    if not row:
        return message
    else:
        return final_message(row, date_format, edit=True)


def final_message(row, date_format=None, *, edit=False):
    if date_format:
        row[2] = row[2].strftime(date_format)
        row[3] = row[3].strftime(date_format)
    return 'Кол-во' * abs(edit-1) + f'сообщений  =>{row[0]}'.capitalize()\
           + '\n'*edit+f'Дата  =>{row[2]}.\n'\
           + 'Кол-во' * abs(edit-1) + f'символов  =>{row[1]}'.capitalize()\
           + '\n'*edit+f'Дата  =>{row[3]}.'


def author_data(ctx, cur, authors):
    try:
        today_data = [authors[ctx.author.id][0], authors[ctx.author.id][1]]
        day_info = f'Кол-во сообщений  =>{today_data[0]}\n' \
                   f'Кол-во символов  =>{today_data[1]}'
    except KeyError:
        day_info = None
        today_data = [0, 0]
    info_dict = {'За всё время':'='*25,
                 lambda: send_data_author_current
                 (cur, ctx, 'logs', 'id', today_data): '='*25,
                 'Текущие показатели пользователя':'='*25,
                 'За сегодня:': day_info,
                 'За неделю:': lambda: send_data_author_current
                 (cur, ctx, 'logs_for_week', 'author_id', today_data),
                 'За месяц:': lambda: send_data_author_current
                 (cur, ctx, 'logs_for_month', 'author_id', today_data),
                 'Максимальные показатели':'='*25,
                 'За день': lambda: send_data_author_max
                 (cur, ctx, 'top_messages_day'),
                 'За месяц': lambda: send_data_author_max
                 (cur, ctx, 'top_messages_month', "%m-%Y"),
                 }
    return info_dict


async def author_data_for_period(ctx, cur, authors, *period):
    info = discord.Embed(title=f'Статистика пользователя',
                         color=discord.Color.green())
    info.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    temp_dict = author_data(ctx, cur, authors)
    info_dict = {}
    for per in period:
        info_dict[f'{per}'] = temp_dict[f'{per}']
    for k, v in {k: v for k, v in info_dict.items() if v}.items():
        if hasattr(k, '__call__'):
            k = k()
        if hasattr(v, '__call__'):
            v = v()
        info.add_field(name=k, value=v, inline=False)
    return await ctx.send(embed=info)


def channel_data(cur):
    info_dict = {
                'Максимальные значения за день': '='*25,
                lambda: send_channel_peak(cur, 'day'): '='*25,
                'Максимальные значения за месяц': '=' * 25,
                lambda: send_channel_peak(cur, 'month', "%m-%Y"): '=' * 25,
                 }

    return info_dict


async def final_stats(info, ctx, func, *args):
    if len(args) == 1:
        info_dict = func(*args)
    else:
        info_dict = func(ctx, *args)
    for k, v in info_dict.items():
        if not v:
            continue
        if hasattr(k, '__call__'):
            k = k()
        if hasattr(v, '__call__'):
            v = v()
        info.add_field(name=k, value=v, inline=False)
    return await ctx.author.send(embed=info)

