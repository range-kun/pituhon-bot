from typing import Type

import sqlalchemy as sa
from sqlalchemy.engine import Connection, Row

from app.log import logger
from app.utils import today
from app.utils.data import Data
from app.utils.data.user_stats import (
    UserMaxStats,
    UserStatsForCurrentMonth,
    UserStatsForCurrentWeek,
)


class MaxServerMessagesForPeriod(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            cls.metadata,
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER),
        )


class MaxServerSymbolsForPeriod(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_symbols_for_period",
            cls.metadata,
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER),
        )


class ServerStats(Data):
    @classmethod
    def compare_and_update_max_stats(
        cls,
        period: str,
        current_amount_of_messages: int,
        current_amount_of_symbols: int,
    ):
        try:
            max_amount_messages_for_period: int = cls.get_max_stats_for_period(
                period,
                MaxServerMessagesForPeriod,
            )[0]
            max_amount_symbols_for_period: int = cls.get_max_stats_for_period(
                period,
                MaxServerSymbolsForPeriod,
            )[0]

        except TypeError:  # data not exists in database
            cls.insert_new_max_stats(period, current_amount_of_messages, MaxServerMessagesForPeriod)
            cls.insert_new_max_stats(period, current_amount_of_symbols, MaxServerSymbolsForPeriod)
            return

        except Exception as e:
            logger.opt(exception=True).error(
                f"Exception occurred {str(e)} while fetching data from databases",
            )
            return "Извините произошла ошибка при попытке получить данных с сервера"

        if current_amount_of_messages > max_amount_messages_for_period:
            cls.update_max_stats(period, current_amount_of_messages, MaxServerMessagesForPeriod)

        if current_amount_of_symbols > max_amount_symbols_for_period:
            cls.update_max_stats(period, current_amount_of_symbols, MaxServerSymbolsForPeriod)

    @classmethod
    def insert_new_max_stats(cls, period, amount, data_class: Type[Data]):
        data_class.insert(period=period, amount=amount, date=today())

    @staticmethod
    def get_max_stats_for_period(period: str, data_class: Type[Data]) -> Row:
        result = data_class.get_data(
            "amount",
            condition=(data_class.get_table().c.period == period),
        )
        result = result.fetchone()
        return result

    @classmethod
    def update_max_stats(cls, period: str, amount: int, data_class: Type[Data]):
        data_class.update(
            condition=(data_class.get_table().c.period == period),
            amount=amount,
            date=today(),
        )

    @classmethod
    def fetch_all_data(cls, connection: Connection):
        messages = MaxServerMessagesForPeriod.get_data(
            "period",
            "date",
            "amount",
            connection=connection,
        ).fetchall()
        symbols = MaxServerSymbolsForPeriod.get_data(
            "period",
            "date",
            "amount",
            connection=connection,
        ).fetchall()
        return messages, symbols

    @classmethod
    def get_server_stats_for_week(cls) -> list[tuple[int]]:
        table = UserStatsForCurrentWeek.get_table()
        return cls.get_server_stats_for_period(table)

    @classmethod
    def get_server_stats_for_month(cls) -> list[tuple[int]]:
        table = UserStatsForCurrentMonth.get_table()
        return cls.get_server_stats_for_period(table)

    @classmethod
    def get_server_stats_for_period(cls, table: sa.Table) -> list[tuple[int]]:
        message_field = table.c["messages"]
        symbol_field = table.c["symbols"]

        with cls.do_with_session() as session:
            channel_info = session.query(sa.func.sum(message_field), sa.func.sum(symbol_field))
            (
                user_with_most_messages,
                user_with_most_symbols,
            ) = UserMaxStats.fetch_users_with_max_stats_for_period(session, table)

        return [channel_info.first(), user_with_most_messages, user_with_most_symbols]

    @staticmethod
    def set_current_stats_for_period_to_zero(period: str):
        if period == "week":
            data_class = UserStatsForCurrentWeek
        elif period == "month":
            data_class = UserStatsForCurrentMonth
        else:
            return
        data_class.update(messages=0, symbols=0)
