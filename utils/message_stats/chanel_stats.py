from datetime import datetime

import discord

from configuration import TEST_CHANNEL_ID
from utils.data.message_stats import MaxServerSymbolsForPeriod, MaxServerMessagesForPeriod, \
    UserStatsForCurrentWeek, UserStatsForCurrentMonth
from utils.message_stats import Statistic
from utils.message_stats import MessageCounter as MC


class ChanelStats(Statistic):
    symbols_for_month = 0
    messages_for_month = 0
    symbols_for_week = 0
    messages_for_week = 0

    @classmethod
    async def daily_routine(cls):
        messages_info, symbols_info = cls.collect_stats_for_day()
        cls.update_max_stats_for_day()
        await cls.send_message_stats_for_day(messages_info, symbols_info)

    @classmethod
    def update_max_stats_for_day(cls):
        cls.update_max_stats("day", MC.messages, MC.symbols)

    @classmethod
    def collect_stats_for_day(cls):
        user_id_with_most_messages = max(MC.authors, key=lambda user: MC.authors[user].amount_of_messages)
        user_with_most_messages = MC.authors[user_id_with_most_messages].amount_of_messages

        user_id_with_most_symbols = max(MC.authors, key=lambda user: MC.authors[user].amount_of_symbols)
        user_with_most_symbols = MC.authors[user_id_with_most_symbols].amount_of_symbols
        return [(user_id_with_most_messages, user_with_most_messages),
                (user_id_with_most_symbols, user_with_most_symbols)
                ]

    @classmethod
    async def send_message_stats_for_day(cls, messages_info, symbols_info):

        output = await cls.create_output_message(
            channel_info=(MC.messages, MC.symbols),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("Всего за день", "Информация по серверу за 24 часа"),
        )

        await cls.channel().send(embed=output)

    @classmethod
    async def weekly_routine(cls):
        messages_info, symbols_info = cls.collect_stats_for_week()

        cls.update_max_stats_for_month()
        await cls.send_message_stats_for_month(messages_info, symbols_info)

    @classmethod
    def collect_stats_for_week(cls) -> tuple:
        channel_info, messages_info, symbols_info = UserStatsForCurrentWeek.get_stats_for_period()
        cls.messages_for_week, cls.symbols_for_week = channel_info
        return messages_info, symbols_info

    @classmethod
    async def send_message_stats_for_week(cls, messages_info: tuple, symbols_info: tuple):

        output = await cls.create_output_message(
            channel_info=(cls.messages_for_month, cls.symbols_for_month),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("Неделя", "Еженедельная информация"),
        )

        await cls.channel().send(embed=output)

    @classmethod
    def update_max_stats_for_week(cls):
        cls.update_max_stats("week", cls.messages_for_week, cls.symbols_for_week)

    @classmethod
    async def monthly_routine(cls):
        day_of_month = datetime.now().day
        if day_of_month == 1:
            messages_info, symbols_info = cls.collect_stats_for_month()
            cls.update_max_stats_for_month()
            await cls.send_message_stats_for_month(messages_info, symbols_info)

    @classmethod
    def collect_stats_for_month(cls) -> tuple:
        channel_info, messages_info, symbols_info = UserStatsForCurrentMonth.get_stats_for_period()
        cls.messages_for_month, cls.symbols_for_month = channel_info
        return messages_info, symbols_info

    @classmethod
    async def send_message_stats_for_month(cls,  messages_info: tuple, symbols_info: tuple):

        output = await cls.create_output_message(
            channel_info=(cls.messages_for_month, cls.symbols_for_month),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("месяц", "Ежемесячная информация"),
        )

        await cls.channel().send(embed=output)

    @classmethod
    def update_max_stats_for_month(cls):
        cls.update_max_stats("month", cls.messages_for_month, cls.symbols_for_month)

    @classmethod
    def channel(cls):
        channel = cls.bot.get_channel(TEST_CHANNEL_ID)  # test mode
        return channel

    @classmethod
    def update_max_stats(
            cls,
            period: str,
            current_amount_of_messages: int,
            current_amount_of_symbols: int
         ):
        max_amount_messages_for_period = MaxServerMessagesForPeriod.get_max_stats_for_period(period)[0]
        max_amount_symbols_for_period = MaxServerSymbolsForPeriod.get_max_stats_for_period(period)[0]

        if current_amount_of_messages > max_amount_messages_for_period:
            MaxServerMessagesForPeriod.update_max_stats(period, MC.messages)

        if current_amount_of_symbols > max_amount_symbols_for_period:
            MaxServerSymbolsForPeriod.update_max_stats(period, MC.symbols)

    @classmethod
    async def create_output_message(cls, *, channel_info, messages_info, symbols_info, period_info):
        user_with_most_symbols, amount_of_symbols_top_user = symbols_info
        user_with_most_messages, amount_of_messages_top_user = messages_info
        amount_of_all_messages, amount_of_all_symbols = channel_info
        name_of_period, description_of_period = period_info

        user_name_with_most_messages = await cls.bot.fetch_user(user_with_most_messages)
        user_name_with_most_messages = user_name_with_most_messages.name
        user_name_with_most_symbols = await cls.bot.fetch_user(user_with_most_symbols)
        user_name_with_most_symbols = user_name_with_most_symbols.name

        channel_info = f'Кол-во сообщений  =>{amount_of_all_messages}\n' \
                       f'Кол-во символов  =>{amount_of_all_symbols}'
        message_info = f'Чемпион по сообщениям => {user_name_with_most_messages}\n' \
                       f'Количество=>{amount_of_messages_top_user}'
        symbol_info = f'Чемпион по символам =>{user_name_with_most_symbols } \n' \
                      f'Количество => {amount_of_symbols_top_user}'
        info_dict = {
            f'Всего за {name_of_period}': '=' * 25,
            channel_info: '=' * 25,
            message_info: '=' * 25,
            symbol_info: '=' * 25
        }

        emb = discord.Embed(title=description_of_period, colour=discord.Color.dark_blue())
        for k, v in info_dict.items():
            emb.add_field(name=k, value=v, inline=False)
        return emb



