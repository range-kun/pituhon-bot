import sqlalchemy as sa
from sqlalchemy import func

from utils.data import Data


class MaxStatsForPeriod(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )

    @classmethod
    def get_max_stats_for_period(cls, period):
        try:
            result = cls.get_data("amount", condition=(cls.get_table().c.period == period))

        except Exception as e:
            print(e)
            return "Извините произошла ошибка при попытке получить данных о сервире"

        result = result.fetchone()
        return result

    @classmethod
    def update_max_stats(cls, period, amount):
        cls.update((cls.get_table().c.period == period), amount=amount)


class MaxServerMessagesForPeriod(MaxStatsForPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_messages_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )


class MaxServerSymbolsForPeriod(MaxStatsForPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "max_server_symbols_for_period",
            sa.MetaData(),
            sa.Column("period", sa.VARCHAR),
            sa.Column("date", sa.DATE),
            sa.Column("amount", sa.INTEGER)
        )


class StatsForCurrentPeriod(Data):

    @classmethod
    def get_stats_for_period(cls) -> list:
        message_field = cls.get_table().c["messages"]
        symbol_field = cls.get_table().c["symbols"]
        user_id_field = cls.get_table().c["user_id"]
        with cls.do_with_session() as session:
            channel_info = session.query(func.sum(message_field), func.sum(symbol_field))
            user_with_most_messages_info = \
                session.query(user_id_field, message_field).order_by(sa.desc(message_field)).limit(1)
            user_with_most_symbols_info = \
                session.query(user_id_field, symbol_field).order_by(sa.desc(symbol_field)).limit(1)

        return [channel_info.first(),
                user_with_most_messages_info.all()[0],
                user_with_most_symbols_info.all()[0]
                ]


class UserStatsForCurrentMonth(StatsForCurrentPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_stats_for_current_month",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("user_id", sa.BIGINT),
        )


class UserStatsForCurrentWeek(StatsForCurrentPeriod):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_stats_for_current_week",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("user_id", sa.BIGINT),
        )
