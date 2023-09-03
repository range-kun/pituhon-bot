from __future__ import annotations

from typing import Type

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.engine import Connection, Row
from sqlalchemy.orm.session import Session

from app.utils import today
from app.utils.data import Data
from app.utils.message_stats_routine import UserStatsForCurrentDay


class UserOverallStats(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        table_name = "user_overall_stats"
        table = cls.metadata.tables.get(table_name)

        if table is not None:
            return table
        return sa.Table(
            table_name,
            cls.metadata,
            sa.Column("user_id", sa.BIGINT, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER),
        )

    @classmethod
    def fetch_overall_data(cls, connection: Connection) -> tuple[int, int]:
        sum_of_messages = cls.fetch_sum_of_messages(connection)
        sum_of_symbols = cls.fetch_sum_of_symbols(connection)
        return sum_of_messages, sum_of_symbols

    @classmethod
    def fetch_sum_of_messages(cls, connection: Connection) -> int:
        messages = cls.get_data("messages", connection=connection).fetchall()
        if messages:
            messages = sum([user_info[0] for user_info in messages])
        return messages

    @classmethod
    def fetch_sum_of_symbols(cls, connection: Connection) -> int:
        symbols = cls.get_data("symbols", connection=connection).fetchall()
        if symbols:
            symbols = sum([user_info[0] for user_info in symbols])
        return symbols


user_overall_stats_table = UserOverallStats.create_table()


class UserStatsForCurrentWeek(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_stats_for_current_week",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserStatsForCurrentMonth(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_stats_for_current_month",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxMessagesForDay(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_day",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxSymbolsForDay(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_day",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxMessagesForWeek(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_week",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxSymbolsForWeek(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_week",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxMessagesForMonth(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_messages_for_month",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("messages", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserMaxSymbolsForMonth(Data):
    @classmethod
    def create_table(cls) -> sa.Table:
        return sa.Table(
            "user_max_symbols_for_month",
            cls.metadata,
            sa.Column("id", sa.INTEGER, primary_key=True),
            sa.Column("symbols", sa.INTEGER),
            sa.Column("record_date", sa.DATE),
            sa.Column("user_id", sa.BIGINT, sa.ForeignKey(user_overall_stats_table.c.user_id)),
        )


class UserCurrentStats(Data):
    user_stats_for_cur_week_table = UserStatsForCurrentWeek.get_table()
    user_stats_for_cur_month_table = UserStatsForCurrentMonth.get_table()

    @classmethod
    def add_or_update_user_stats(
        cls,
        users_stats_for_new_day: dict[int, UserStatsForCurrentDay],
        user_stats_class: Type[Data],
        connection: Connection,
    ):
        users_db_data = cls.fetch_users_current_stats_for_period(user_stats_class, connection)

        users_dict_db_data = {
            user_id: UserStatsForCurrentDay(amount_of_symbols=symbols, amount_of_messages=messages)
            for user_id, messages, symbols in users_db_data
        }
        users_db_ids = [user[0] for user in users_db_data]

        for user_id in users_stats_for_new_day:
            user = users_stats_for_new_day[user_id]

            if user_id in users_db_ids:
                messages = user.amount_of_messages + users_dict_db_data[user_id].amount_of_messages
                symbols = user.amount_of_symbols + users_dict_db_data[user_id].amount_of_symbols
                user_stats_class.update(
                    connection=connection,
                    condition=(user_stats_class.get_table().c.user_id == user_id),
                    messages=messages,
                    symbols=symbols,
                )
            else:
                user_stats_class.insert(
                    connection=connection,
                    user_id=user_id,
                    messages=user.amount_of_messages,
                    symbols=user.amount_of_symbols,
                )

    @classmethod
    def fetch_users_current_stats_for_period(
        cls,
        user_stats_class: Type[Data],
        connection: Connection = None,
    ) -> list[Row]:  # return list of users amount of messages and symbols
        users_db_data = (
            user_stats_class.get_data(
                "user_id",
                "messages",
                "symbols",
                connection=connection,
            ).fetchall()
            or []
        )
        return users_db_data

    @classmethod
    def fetch_single_user_db_stats(cls, session: Session, user_id: int) -> list[int]:
        required_data = [
            cls.user_stats_for_cur_month_table.c.messages,
            cls.user_stats_for_cur_month_table.c.symbols,
            cls.user_stats_for_cur_week_table.c.messages,
            cls.user_stats_for_cur_week_table.c.symbols,
        ]
        user_overall_id_field = user_overall_stats_table.c.user_id
        week_condition = user_overall_id_field == cls.user_stats_for_cur_week_table.c.user_id
        month_condition = user_overall_id_field == cls.user_stats_for_cur_month_table.c.user_id
        user_filter = user_overall_id_field == user_id

        user_data = (
            session.query(user_overall_stats_table, *required_data)
            .join(cls.user_stats_for_cur_month_table, month_condition)
            .join(cls.user_stats_for_cur_week_table, week_condition)
            .filter(user_filter)
            .all()
        )

        return list(user_data[0][1:]) if user_data else user_data


class UserMaxStats(Data):
    max_tables = None
    user_max_stats_for_day = (UserMaxMessagesForDay, UserMaxSymbolsForDay)
    user_max_stats_for_week = (UserMaxMessagesForWeek, UserMaxSymbolsForWeek)
    user_max_stats_for_month = (UserMaxMessagesForMonth, UserMaxSymbolsForMonth)

    @classmethod
    def compare_and_update_users_max_info(
        cls,
        users_old_data: dict[int, UserStatsForCurrentDay],
        users_new_data: dict[int, UserStatsForCurrentDay],
        period: str,
    ):
        message_class, symbols_class = cls.define_users_classes(period)
        if not message_class:
            return

        with cls.begin() as connection:
            for user_id, user_new_data in users_new_data.items():
                user_old_data = users_old_data.get(user_id)
                if not user_old_data:
                    cls.add_new_max_user_stats(
                        user_id,
                        user_new_data,
                        connection,
                        message_class,
                        symbols_class,
                    )
                    continue
                if user_old_data.amount_of_messages == -100:
                    cls.add_new_max_user_stats(
                        user_id,
                        user_new_data,
                        connection,
                        message_class=message_class,
                    )
                    continue

                if user_old_data.amount_of_symbols == -100:
                    cls.add_new_max_user_stats(
                        user_id,
                        user_new_data,
                        connection,
                        symbols_class=symbols_class,
                    )
                    continue

                if user_new_data.amount_of_messages > user_old_data.amount_of_messages:
                    message_class.update(
                        connection=connection,
                        condition=(message_class.get_table().c.user_id == user_id),
                        messages=user_new_data.amount_of_messages,
                        record_date=today(),
                    )

                if user_new_data.amount_of_symbols > user_old_data.amount_of_symbols:
                    symbols_class.update(
                        connection=connection,
                        condition=(symbols_class.get_table().c.user_id == user_id),
                        symbols=user_new_data.amount_of_symbols,
                        record_date=today(),
                    )

    @classmethod
    def add_new_max_user_stats(
        cls,
        user_id: int,
        user_data: UserStatsForCurrentDay,
        connection: Connection = None,
        message_class: Type[Data] = None,
        symbols_class: Type[Data] = None,
    ):
        if user_data.amount_of_messages > 0 and message_class:
            message_class.insert(
                connection=connection,
                user_id=user_id,
                messages=user_data.amount_of_messages,
                record_date=today(),
            )
        if user_data.amount_of_symbols > 0 and symbols_class:
            symbols_class.insert(
                connection=connection,
                user_id=user_id,
                symbols=user_data.amount_of_symbols,
                record_date=today(),
            )

    @classmethod
    def fetch_user_db_max_stats(cls, session: Session, user_id: int) -> list[int]:
        required_data = []
        max_tables = cls.create_max_tables()
        msg_fields = ["messages", "record_date"]
        symbols_fields = ["symbols", "record_date"]

        for period_tables in max_tables:
            required_data.extend(
                cls.define_required_fields(period_tables, msg_fields, symbols_fields),
            )

        user_overall_id_field = user_overall_stats_table.c.user_id
        user_data_query = session.query(user_overall_stats_table.c.user_id, *required_data)
        for message_table, symbols_table in max_tables:
            user_data_query = user_data_query.join(
                message_table,
                user_overall_id_field == message_table.c.user_id,
                isouter=True,
            )
            user_data_query = user_data_query.join(
                symbols_table,
                user_overall_id_field == symbols_table.c.user_id,
                isouter=True,
            )
        user_data = user_data_query.filter(user_overall_id_field == user_id).all()
        return list(user_data[0][1:]) if user_data else []

    @classmethod
    def get_all_users_max_stats(cls, period: str) -> tuple[list[tuple[int]], list[tuple[int]]]:
        message_class, symbols_class = cls.define_users_classes(period)

        with cls.begin() as connection:
            messages_info = message_class.get_data(
                "user_id",
                "messages",
                connection=connection,
            ).fetchall()
            symbols_info = symbols_class.get_data(
                "user_id",
                "symbols",
                connection=connection,
            ).fetchall()
        return messages_info, symbols_info

    @classmethod
    def fetch_champions_stats(cls) -> list[tuple[int, int]]:
        champs_stats = []
        with cls.do_with_session() as session:
            max_tables = cls.create_max_tables()
            for message_table, symbol_table in max_tables:
                message_stats, symbols_stats = cls.fetch_users_with_max_stats_for_period(
                    session,
                    message_table,
                    symbol_table,
                )
                champs_stats.append(message_stats)
                champs_stats.append(symbols_stats)
        return champs_stats

    @classmethod
    def fetch_users_with_max_stats_for_period(
        cls,
        session: Session,
        message_table: sa.Table,
        symbols_table: sa.Table = None,
    ) -> tuple[tuple[int], tuple[int]]:
        if symbols_table is None:
            symbols_table = message_table
        user_with_most_messages_info = cls.fetch_user_with_max_messages(session, message_table)

        if user_with_most_messages_info:
            user_with_most_messages_info = user_with_most_messages_info[0]

        user_with_most_symbols_info = cls.fetch_user_with_max_symbols(session, symbols_table)
        if user_with_most_symbols_info:
            user_with_most_symbols_info = user_with_most_symbols_info[0]

        return user_with_most_messages_info, user_with_most_symbols_info

    @classmethod
    def fetch_user_with_max_symbols(cls, session: Session, table: sa.Table) -> list[tuple]:
        symbol_field = table.c["symbols"]
        user_id_field = table.c["user_id"]
        user_with_most_symbols = (
            session.query(user_id_field, symbol_field).order_by(sa.desc(symbol_field)).limit(1)
        )
        return user_with_most_symbols.all()

    @classmethod
    def fetch_user_with_max_messages(cls, session: Session, table: sa.Table) -> list[tuple]:
        message_field = table.c["messages"]
        user_id_field = table.c["user_id"]
        user_with_most_messages = (
            session.query(user_id_field, message_field).order_by(sa.desc(message_field)).limit(1)
        )
        return user_with_most_messages.all()

    @classmethod
    def define_users_classes(cls, period: str) -> tuple[Type[Data], Type[Data]] | tuple[None, None]:
        if period == "day":
            message_class, symbols_class = cls.user_max_stats_for_day
        elif period == "week":
            message_class, symbols_class = cls.user_max_stats_for_week
        elif period == "month":
            message_class, symbols_class = cls.user_max_stats_for_month
        else:
            return None, None

        return message_class, symbols_class

    @classmethod
    def define_required_fields(
        cls,
        max_tables: list[sa.Table],
        msg_fields: list[str],
        symbols_fields: list[str],
    ) -> list[Column]:
        required_fields = []

        messages_table, symbol_table = max_tables
        msg_table_fields = [messages_table.c[field] for field in msg_fields]
        symbols_table_fields = [symbol_table.c[field] for field in symbols_fields]
        required_fields += msg_table_fields + symbols_table_fields
        return required_fields

    @classmethod
    def create_max_tables(cls) -> list[list[sa.Table]]:
        if cls.max_tables is None:
            max_tables = []
            for period in ["day", "week", "month"]:
                max_classes = cls.define_users_classes(period)
                max_tables.append([max_class.get_table() for max_class in max_classes])
            cls.max_tables = max_tables
        return cls.max_tables
