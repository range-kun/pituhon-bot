from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from utils.data import Data
from utils import today


class UserOverallStats(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_overall_stats",
            sa.MetaData(),
            sa.Column("user_id", sa.BIGINT, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER)
        )


class UserStatsForCurrentWeek(Data):

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


class UserStatsForCurrentMonth(Data):

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


class UserMaxMessagesForDay(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_day",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxSymbolsForDay(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_day",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxMessagesForWeek(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_week",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxSymbolsForWeek(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_week",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxMessagesForMonth(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_month",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxSymbolsForMonth(Data):

    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_month",
            sa.MetaData(),
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey("user_overall_stats.id"))
        )


class UserMaxStats(Data):
    user_max_stats_for_day = (UserMaxMessagesForDay, UserMaxSymbolsForDay)
    user_max_stats_for_week = (UserMaxMessagesForWeek, UserMaxSymbolsForWeek)
    user_max_stats_for_month = (UserMaxMessagesForMonth, UserMaxSymbolsForDay)

    @classmethod
    def get_old_max_user_data_for_period(cls, period: str) -> tuple[list, list]:
        message_class, symbols_class = cls.define_users_classes(period)

        with cls.begin() as connection:
            messages_info = message_class.get_data("user_id", "messages", connection=connection).fetchall()
            symbols_info = symbols_class.get_data("user_id", "symbols", connection=connection).fetchall()
        return messages_info, symbols_info

    @classmethod
    def add_new_max_user_stats(cls, period: str, user_id: int, user_data, connection: Connection = None):
        message_class, symbols_class = cls.define_users_classes(period)

        if not message_class:
            return

        message_class.insert(
            connection=connection,
            user_id=user_id,
            messages=user_data.amount_of_symbols,
            record_date=today()
        )
        symbols_class.insert(
            connection=connection,
            user_id=user_id,
            symbols=user_data.amount_of_symbols,
            record_date=today()
        )

    @classmethod
    def define_users_classes(cls, period):
        if period == "day":
            message_class, symbols_class = cls.user_max_stats_for_day
        elif period == "week":
            message_class, symbols_class = cls.user_max_stats_for_week
        elif period == "month":
            message_class, symbols_class = cls.user_max_stats_for_month
        else:
            return None, None

        return message_class, symbols_class
