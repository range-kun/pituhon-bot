import discord

from configuration import TEST_CHANNEL_ID
from utils import is_last_month_day, catch_exception
from utils.data.channel_stats import ServerStats

from utils.message_stats_routine import Statistic, MessageDayCounter as MDC


class ChanelStats(Statistic):
    symbols_for_month = 0
    messages_for_month = 0
    symbols_for_week = 0
    messages_for_week = 0

    @classmethod
    @catch_exception
    async def daily_routine(cls):
        if not MDC.messages:
            return
        messages_champ, symbols_champ = cls.collect_stats_for_day()
        cls.update_max_stats_for_day()
        await cls.send_message_stats_for_day(messages_champ, symbols_champ)

    @classmethod
    @catch_exception
    async def weekly_routine(cls):
        messages_info, symbols_info = cls.collect_stats_for_week()
        if not messages_info:
            return
        cls.update_max_stats_for_week()
        await cls.send_message_stats_for_week(messages_info, symbols_info)
        cls.set_week_current_stats_to_zero()

    @classmethod
    @catch_exception
    async def monthly_routine(cls):
        if not is_last_month_day():
            return
        messages_info, symbols_info = cls.collect_stats_for_month()
        if not messages_info:
            return
        cls.update_max_stats_for_month()
        await cls.send_message_stats_for_month(messages_info, symbols_info)
        cls.set_month_current_stats_to_zero()

    @classmethod
    def collect_stats_for_day(cls) -> tuple:
        messages_champ, symbols_champ = MDC.get_server_champ_for_today()
        return messages_champ, symbols_champ

    @classmethod
    def collect_stats_for_week(cls) -> tuple:
        channel_info, messages_info, symbols_info = ServerStats.get_server_stats_for_week()
        cls.messages_for_week, cls.symbols_for_week = channel_info
        return messages_info, symbols_info

    @classmethod
    def collect_stats_for_month(cls) -> tuple:
        channel_info, messages_info, symbols_info = ServerStats.get_server_stats_for_month()
        cls.messages_for_month, cls.symbols_for_month = channel_info
        return messages_info, symbols_info

    @classmethod
    def update_max_stats_for_day(cls):
        cls.update_max_stats("day", MDC.messages, MDC.symbols)

    @classmethod
    def update_max_stats_for_week(cls):
        cls.update_max_stats("week", cls.messages_for_week, cls.symbols_for_week)

    @classmethod
    def update_max_stats_for_month(cls):
        cls.update_max_stats("month", cls.messages_for_month, cls.symbols_for_month)

    @classmethod
    def set_week_current_stats_to_zero(cls):
        cls.symbols_for_week = 0
        cls.messages_for_week = 0
        ServerStats.set_current_stats_for_period_to_zero("week")

    @classmethod
    def set_month_current_stats_to_zero(cls):
        cls.symbols_for_month = 0
        cls.messages_for_month = 0
        ServerStats.set_current_stats_for_period_to_zero("month")

    @classmethod
    def update_max_stats(
            cls,
            period: str,
            current_amount_of_messages: int,
            current_amount_of_symbols: int
         ):
        ServerStats.compare_and_update_max_stats(period, current_amount_of_messages, current_amount_of_symbols)

    @classmethod
    async def send_message_stats_for_day(cls, messages_info: tuple[int], symbols_info: tuple[int]):
        output = await cls.create_output_message(
            channel_info=(MDC.messages, MDC.symbols),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("Всего за день", "Информация по серверу за 24 часа"),
        )

        await cls.channel().send(embed=output)

    @classmethod
    async def send_message_stats_for_week(cls, messages_info: tuple, symbols_info: tuple):

        output = await cls.create_output_message(
            channel_info=(cls.messages_for_week, cls.symbols_for_week),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("неделю", "Еженедельная информация"),
        )

        await cls.channel().send(embed=output)

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
        symbol_info = f'Чемпион по символам =>{user_name_with_most_symbols} \n' \
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

    @classmethod
    def channel(cls):
        channel = cls.bot.get_channel(TEST_CHANNEL_ID)  # test mode
        return channel
