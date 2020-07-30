import time
from datetime import datetime, timedelta
import discord


def yesterday():
    return datetime.date(datetime.now() - timedelta(days=1))


async def send_data_for_day(channel, authors, messages, symbols, client):
    emb = discord.Embed(title='Информация по серверу за 24 часа', colour=discord.Color.dark_blue())
    temp_list_messages = sorted(list(authors.items()),
                                key=lambda i: i[1][0], reverse=True)[0]
    temp_list_symbols = sorted(list(authors.items()),
                               key=lambda i: i[1][1], reverse=True)[0]
    author_m, author_s = [i.name for i in
                          map(client.get_user, [temp_list_messages[0], temp_list_symbols[0]])]
    channel_info = f'Кол-во сообщений  =>{messages}\n' \
                   f'Кол-во символов  =>{symbols}'
    message_info = f'Чемпион по сообщениям => {author_m}\n' \
                   f'Количество=>{temp_list_messages[1][0]}'
    symbol_info = f'Чемпион по символам =>{author_s} \n' \
                  f'Количество => {temp_list_symbols[1][1]}'
    info_dict = {'Всего за день': '='*25, channel_info: '='*25,
                 message_info: '='*25, symbol_info: '='*25}
    for k, v in info_dict.items():
        emb.add_field(name=k, value=v, inline=False)
    await channel.send(embed=emb)


def update_stats_author_day(conn, cur, authors):
    for i, v in authors.items():
        cur.execute(f'SELECT MESSAGES, SYMBOLS FROM LOGS WHERE ID={i}')
        row = cur.fetchone()
        update_dict = {'LOGS': 'ID', 'logs_for_week': 'author_id', 'logs_for_month': 'author_id'}
        if not row:
            for table, id_num in update_dict.items():
                cur.execute(f"INSERT INTO {table} ({id_num}, MESSAGES, SYMBOLS) "
                            f"VALUES ({i}, '{v[0]}', {v[1]})")
        else:
            for table, id_num in update_dict.items():
                cur.execute(f'SELECT MESSAGES, SYMBOLS FROM {table} WHERE {id_num}={i}')
                row_1 = cur.fetchone()
                try:
                    temp = tuple(b + x for b, x in zip(row_1, v))
                except Exception:
                    cur.execute(f"INSERT INTO {table} ({id_num}, MESSAGES, SYMBOLS) VALUES "
                                f"({i}, '{temp[0]}', {temp[1]})")
                else:
                    cur.execute(f"UPDATE {table} SET messages={temp[0]}, symbols={temp[1]} \
                                WHERE {id_num}={i}")
        conn.commit()
        update_author_max_stats(cur, 'top_messages_day', i, v)


def update_author_max_stats(cur, table, id_num, values):
    cur.execute(f'SELECT MESSAGES, SYMBOLS FROM {table} WHERE author_id={id_num}')
    new_messages, new_symbols = values
    try:
        top_messages, top_symbols = cur.fetchone()
    except TypeError:
        cur.execute(f"INSERT INTO {table} (author_id, MESSAGES, SYMBOLS, top_messages_date, top_symbols_date) "
                    f"VALUES ({id_num}, {new_messages}, {new_symbols}, '{yesterday()}', '{yesterday()}')")
    else:
        if new_messages > top_messages:
            cur.execute(f"UPDATE {table} SET messages={new_messages}, "
                        f"top_messages_date='{yesterday()}' where author_id={id_num}")
        if new_symbols > top_symbols:
            cur.execute(f"UPDATE {table} SET symbols={new_symbols}, "
                        f"top_symbols_date='{yesterday()}' where author_id={id_num}")


async def send_data_schedule(cur, channel, client):
    send_data_list = {'logs_for_month': [time.localtime()[2] == 1,
                                         'Ежемесячная информация', 'месяц'],
                      'logs_for_week': [datetime.today().isoweekday() == 1,
                                        'Еженедельная информация', 'неделю']}
    for key, value in send_data_list.items():
        if value[0]:
            cur.execute(f"SELECT SUM(messages), SUM(symbols) from {key}")
            messages_for_period, symbols_for_period = cur.fetchone()
            if messages_for_period:
                emb = discord.Embed(title=value[1], colour=discord.Color.dark_blue())
                cur.execute(f"SELECT author_id, messages from {key} order by messages DESC")
                author_top_m, top_messages = cur.fetchone()
                cur.execute(f"SELECT author_id, symbols from {key} order by symbols DESC")
                author_top_s, top_symbols = cur.fetchone()
                author_top_m, author_top_s = [i.name for i in
                                              map(client.get_user, [author_top_m, author_top_s])]
                channel_info = f'Кол-во сообщений  =>{messages_for_period}\n' \
                               f'Кол-во символов  =>{symbols_for_period}'
                message_info = f'Чемпион по сообщениям => {author_top_m}\n' \
                               f'Количество=>{top_messages}'
                symbol_info = f'Чемпион по символам =>{author_top_s} \n' \
                              f'Количество => {top_symbols}'
                info_dict = {f'Всего за {value[2]}': '=' * 25, channel_info: '=' * 25,
                             message_info: '=' * 25, symbol_info: '=' * 25}
                for k, v in info_dict.items():
                    emb.add_field(name=k, value=v, inline=False)
                await channel.send(embed=emb)


def update_stats_schedule(cur):
    cur.execute(f'SELECT ID FROM LOGS')
    row = (i[0] for i in cur.fetchall())
    update_data_list = {'top_messages_month': [time.localtime()[2] == 1, 'logs_for_month']}
    for key, value in update_data_list.items():
        if value[0]:
            for i in row:
                cur.execute(f"SELECT messages, symbols from {value[1]} where author_id={i} and messages>0")
                row = cur.fetchone()
                if row:
                    update_author_max_stats(cur, key, i, row)


def update_stats_max_day(cur, messages, symbols):
    cur.execute("SELECT MESSAGES, SYMBOLS FROM ACTIVITY where period='day'")
    temp_mes, temp_symb = cur.fetchone()
    if messages > temp_mes:
        cur.execute(f"UPDATE activity SET DATE_PEAK_MESSAGES='{yesterday()}', MESSAGES={messages} where period='day'")
    elif symbols > temp_symb:
        cur.execute(f"UPDATE activity SET DATE_PEAK_SYMBOLS='{yesterday()}', SYMBOLS={symbols}  where period='day'")


def update_stats_max_month(cur):
    cur.execute("SELECT MESSAGES, SYMBOLS FROM ACTIVITY where period='month'")
    old_mes, old_symb = cur.fetchone()
    cur.execute('SELECT SUM(MESSAGES), SUM(SYMBOLS) FROM logs_for_month')
    new_mes, new_symb = cur.fetchone()
    if new_mes > old_mes:
        cur.execute(f"UPDATE activity SET DATE_PEAK_MESSAGES='{yesterday()}',"
                    f" MESSAGES={new_mes} where period='month'")
    elif new_symb > old_symb:
        cur.execute(f"UPDATE activity SET DATE_PEAK_SYMBOLS='{yesterday()}', "
                    f"SYMBOLS={new_symb} where period='month'")


#########stats############

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
                'Максимальные значения за день':'='*25,
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
    for k, v in {k: v for k, v in info_dict.items() if v}.items():
        if hasattr(k, '__call__'):
            k = k()
        if hasattr(v, '__call__'):
            v = v()
        info.add_field(name=k, value=v, inline=False)
    return await ctx.send(embed=info)

