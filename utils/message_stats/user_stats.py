from __future__ import annotations

from itertools import groupby
from typing import Type, Optional

from sqlalchemy.engine import Connection


from utils import today, is_last_month_day
from utils.message_stats import UserStatsForCurrentDay, Statistic, MessageCounter as MC
from utils.data.user_stats import Data, UserOverallStats, UserStatsForCurrentWeek, UserStatsForCurrentMonth, \
    UserMaxStats


class UserStats(Statistic):

    @classmethod
    async def daily_routine(cls):
        cls.update_users_stats_by_end_of_day()
        cls.update_user_max_stats_for_period("day")

    @classmethod
    async def weekly_routine(cls):
        cls.update_user_max_stats_for_period("week")

    @classmethod
    async def monthly_routine(cls):

        if is_last_month_day():
            cls.update_user_max_stats_for_period("month")

    @classmethod
    def update_users_stats_by_end_of_day(cls):
        with UserMaxStats.begin() as connect:
            for user_stats_class in [UserOverallStats, UserStatsForCurrentWeek, UserStatsForCurrentMonth]:
                cls.add_or_update_user_stats(MC.authors, user_stats_class, connect)

    @classmethod
    def add_or_update_user_stats(
            cls,
            users_stats_for_new_day: dict[int, UserStatsForCurrentDay],
            user_stats_class: Type[Data],
            connection: Connection
    ):

        users_db_data = cls.get_db_current_users_stats(user_stats_class, connection)

        users_dict_db_data = {user_id: UserStatsForCurrentDay(amount_of_symbols=symbols, amount_of_messages= messages)
                              for user_id, messages, symbols in users_db_data}
        users_db_id = [user[0] for user in users_db_data]

        for user_id in users_stats_for_new_day:

            if user_id in users_db_id:
                messages = users_stats_for_new_day[user_id].amount_of_messages \
                           + users_dict_db_data[user_id].amount_of_messages
                symbols = users_stats_for_new_day[user_id].amount_of_symbols \
                          + users_dict_db_data[user_id].amount_of_symbols
                user_stats_class.update(
                    condition=(user_stats_class.get_table().c.user_id == user_id),
                    connection=connection,
                    messages=messages,
                    symbols=symbols
                )
            else:
                user_stats_class.insert(
                    connection=connection,
                    user_id=user_id,
                    messages=messages,
                    symbols=symbols
                )

    @classmethod
    def update_user_max_stats_for_period(cls, period: str):
        users_new_data = cls.get_current_users_stats(period)
        if not users_new_data:
            return

        messages_info, symbols_info = UserMaxStats.get_old_max_user_data_for_period(period)
        grouped_old_user_info = cls.group_users_stats(messages_info, symbols_info)
        cls.compare_and_update_users_info(grouped_old_user_info, users_new_data, period)

    @classmethod
    def get_current_users_stats(cls,
                                period: str) -> Optional[dict[int, UserStatsForCurrentDay]]:
        users_info = {}
        if period == "day":
            return MC.authors
        elif period == "week":
            result = cls.get_db_current_users_stats(UserStatsForCurrentWeek)
        elif period == "month":
            result = cls.get_db_current_users_stats(UserStatsForCurrentMonth)
        else:
            return

        for user_id, messages, symbols in result:
            users_info[user_id] = UserStatsForCurrentDay(
                amount_of_symbols=symbols,
                amount_of_messages=messages
            )
        return users_info

    @classmethod
    def get_db_current_users_stats(cls,
                                   user_stats_class: Type[Data],
                                   connection: Connection = None) -> list:
        users_db_data = user_stats_class.get_data(
            "user_id",
            "messages",
            "symbols",
            connection=connection).fetchall() or []
        return users_db_data

    @classmethod
    def group_users_stats(cls, messages_info: list, symbols_info: list) -> dict[int, UserStatsForCurrentDay]:
        id_func = lambda user_data: user_data[0]
        users_db_info = sorted(messages_info + symbols_info, key=id_func)

        users_info = {}
        for user_id, users_stats_info in groupby(users_db_info, key=id_func):
            messages, symbols = [user_stats[1] for user_stats in users_stats_info]
            if messages < symbols:
                messages, symbols = symbols, messages
            users_info[user_id] = UserStatsForCurrentDay(
                amount_of_symbols=symbols,
                amount_of_messages=messages
            )
        return users_info

    @classmethod
    def compare_and_update_users_info(
            cls,
            users_old_data: dict[int, UserStatsForCurrentDay],
            users_new_data: dict[int, UserStatsForCurrentDay],
            period: str
    ):

        message_class, symbols_class = UserMaxStats.define_users_classes(period)

        with UserMaxStats.begin() as connection:

            for user_id, user_new_data in users_new_data.items():
                user_old_data = users_old_data.get(user_id)
                if users_old_data is None:
                    UserMaxStats.add_new_max_user_stats(period, user_id, users_new_data, connection)
                    continue

                if user_new_data.amount_of_messages > user_old_data.amount_of_messages:
                    message_class.insert(connection=connection,
                                         user_id=user_id,
                                         messages=user_new_data.amount_of_messages,
                                         record_date=today()
                                         )

                if user_new_data.amount_of_symbols > user_old_data.amount_of_symbols:
                    symbols_class.insert(connection=connection,
                                         user_id=user_id,
                                         symbols=user_new_data.amount_of_symbols,
                                         record_date=today()
                                         )
