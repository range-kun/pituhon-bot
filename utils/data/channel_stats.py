from typing import Type

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from utils.data import Data
from utils.data.user_stats import UserStatsForCurrentWeek, UserStatsForCurrentMonth, UserMaxStats


class MaxServerMessagesForPeriod(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )


class MaxServerSymbolsForPeriod(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_symbols_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )


class ServerStats(Data):
    @classmethod
    def compare_and_update_max_stats(
            cls,
            period: str,
            current_amount_of_messages: int,
            current_amount_of_symbols: int
    ):
        try:
            max_amount_messages_for_period = cls.get_max_stats_for_period(period, MaxServerMessagesForPeriod)[0]
            max_amount_symbols_for_period = cls.get_max_stats_for_period(period, MaxServerSymbolsForPeriod)[0]
        except Exception as e:
            print(e)
            return "Извините произошла ошибка при попытке получить данных о сервере"

        if current_amount_of_messages > max_amount_messages_for_period:
            cls.update_max_stats(period, current_amount_of_messages, MaxServerMessagesForPeriod)

        if current_amount_of_symbols > max_amount_symbols_for_period:
            cls.update_max_stats(period, current_amount_of_symbols, MaxServerSymbolsForPeriod)

    @classmethod
    def get_max_stats_for_period(cls, period: str, data_class: Type[Data]) -> list[int]:

        result = data_class.get_data("amount", condition=(data_class.get_table().c.period == period))
        result = result.fetchone()
        return result

    @classmethod
    def update_max_stats(cls, period, amount, data_class: Type[Data]):
        data_class.update(condition=(data_class.get_table().c.period == period), amount=amount)

    @classmethod
    def fetch_all_data(cls, connection: Connection):
        messages = MaxServerMessagesForPeriod.get_data("period", "date", "amount", connection=connection).fetchall()
        symbols = MaxServerSymbolsForPeriod.get_data("period", "date", "amount", connection=connection).fetchall()
        return messages, symbols

    @classmethod
    def get_server_stats_for_week(cls):
        table = UserStatsForCurrentWeek.get_table()
        return cls.get_server_stats_for_period(table)

    @classmethod
    def get_server_stats_for_month(cls):
        table = UserStatsForCurrentMonth.get_table()
        return cls.get_server_stats_for_period(table)

    @classmethod
    def get_server_stats_for_period(cls, table: sa.Table) -> list:
        message_field = table.c["messages"]
        symbol_field = table.c["symbols"]

        with cls.do_with_session() as session:
            channel_info = session.query(
                sa.func.sum(message_field),
                sa.func.sum(symbol_field)
            )
            user_with_most_messages, user_with_most_symbols = \
                UserMaxStats.fetch_users_with_max_stats_for_period(session, table)

        return [
            channel_info.first(),
            user_with_most_messages,
            user_with_most_symbols
        ]

    @classmethod
    def set_current_stats_for_period_to_zero(cls, period: str):
        if period == "week":
            data_class = UserStatsForCurrentWeek
        elif period == "month":
            data_class = UserStatsForCurrentMonth
        else:
            return

        data_class.update(messages=0, symbols=0)
