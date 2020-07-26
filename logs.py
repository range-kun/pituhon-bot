import time
from datetime import datetime, timedelta


def yesterday():
    return datetime.date(datetime.now() - timedelta(days=1))


async def send_data_for_day(channel, authors, messages, symbols):
    temp_dict_messages = sorted(list(authors.items()),
                                key=lambda i: i[1][0], reverse=True)[0]
    temp_dict_symbols = sorted(list(authors.items()),
                               key=lambda i: i[1][1], reverse=True)[0]
    await channel.send(f'Всего за день было написано {messages} сообщений, '
                       f'с общим количеством символов равным {symbols}.\n'
                       f'Наибольшее количество сообщений: {temp_dict_messages[1][0]}'
                       f' было написано <@{temp_dict_messages[0]}>\n'
                       f'Наибольшее количество символов: {temp_dict_symbols[1][1]}'
                       f' было написано <@{temp_dict_symbols[0]}>')


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


async def send_data_schedule(cur, channel):
    send_data_list = {'logs_for_month': [time.localtime()[2] == 1, 'месяц'],
                      'logs_for_week': [datetime.today().isoweekday() == 1, 'неделю']}
    for key, value in send_data_list.items():
        if value[0]:
            cur.execute(f"SELECT SUM(messages), SUM(symbols) from {key}")
            messages_for_period, symbols_for_period = cur.fetchone()
            cur.execute(f"SELECT author_id, messages from {key} order by messages DESC")
            author_top_m, top_messages = cur.fetchone()
            cur.execute(f"SELECT author_id, symbols from {key} order by symbols DESC")
            author_top_s, top_symbols = cur.fetchone()
            await channel.send(f'Всего за {value[1]} было написано {messages_for_period} сообщений, '
                               f'с общим количеством символов равным {symbols_for_period}.\n'
                               f'Наибольшее количество сообщений: {top_messages}'
                               f' было написано <@{author_top_m}>\n'
                               f'Наибольшее количество символов: {top_symbols}'
                               f' было написано <@{author_top_s}>')


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


async def send_data_peak(cur, ctx, period, duration, date_format=None):
    cur.execute(f"SELECT messages, symbols, date_peak_messages, date_peak_symbols"
                f" FROM ACTIVITY WHERE PERIOD='{period}'")
    row = list(cur.fetchone())
    if date_format:
        row[2] = row[2].strftime(date_format)
        row[3] = row[3].strftime(date_format)
    return await final_message(ctx, row, duration)


async def final_message(ctx, row, duration, author_name=False):
    name = f"пользователем <@{ctx.author.id}> "
    return await ctx.send(f'Наибольшее количество сообщений {name*author_name}за {duration} '
                          f'было написано {row[2]}, с общим количеством {row[0]}.\n'
                          f'Наибольшее количество символов за {duration}'
                          f'было написано {row[3]}, с общим количеством {row[1]}.')


async def send_data_author_current(cur, ctx, table, duration, id_num):
    cur.execute(f'SELECT MESSAGES,SYMBOLS FROM {table} where {id_num}={ctx.author.id}')
    row = cur.fetchone()
    if not row:
        return await ctx.send(f'{ctx.author.name} статистика на ваше не была обноружена в базе данных,'
                              f'повторите попытку в начале следующего дня')
    else:
        return await ctx.send(f'{ctx.author.name} за {duration} было написано всего {row[0]} сообщений. '
                              f'С общим количеством символов {row[1]} ')


async def send_data_author_max(cur, ctx, table, duration, date_format=None):
    cur.execute(f"SELECT messages, symbols, top_messages_date, top_symbols_date"
                f" from {table} where author_id={ctx.author.id}")
    row = list(cur.fetchone())
    if date_format:
        row[2] = row[2].strftime(date_format)
        row[3] = row[3].strftime(date_format)
    if not row:
        return await ctx.send(f'{ctx.author.name} статистика на ваше не была обноружена в базе данных,'
                              f'повторите попытку в начале следующего дня')
    else:
        return await final_message(ctx, row, duration, True)
