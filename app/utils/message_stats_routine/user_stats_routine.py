from __future__ import annotations

from typing import Optional


from app.utils import is_last_month_day, catch_exception
from app.utils.message_stats_routine import UserStatsForCurrentDay, Statistic, MessageDayCounter as MDC
from app.utils.data.user_stats import UserOverallStats, UserStatsForCurrentWeek, UserStatsForCurrentMonth, \
    UserMaxStats, UserCurrentStats


class UserStats(Statistic):

    @classmethod
    @catch_exception
    async def daily_routine(cls):
        cls.update_users_stats_by_end_of_day()
        cls.update_user_max_stats_for_period("day")

    @classmethod
    @catch_exception
    async def weekly_routine(cls):
        cls.update_user_max_stats_for_period("week")

    @classmethod
    @catch_exception
    async def monthly_routine(cls):
        if not is_last_month_day():
            return
        cls.update_user_max_stats_for_period("month")

    @classmethod
    def update_users_stats_by_end_of_day(cls):
        with UserMaxStats.begin() as connect:
            for user_stats_class in [UserOverallStats, UserStatsForCurrentWeek, UserStatsForCurrentMonth]:
                UserCurrentStats.add_or_update_user_stats(MDC.authors, user_stats_class, connect)

    @classmethod
    def update_user_max_stats_for_period(cls, period: str):
        users_new_data = cls.get_current_users_stats(period)
        if not users_new_data:
            return

        messages_info, symbols_info = UserMaxStats.get_all_users_max_stats(period)
        if messages_info or symbols_info:
            grouped_old_user_info = cls.group_users_stats(messages_info, symbols_info)
        else:
            grouped_old_user_info = {}
        UserMaxStats.compare_and_update_users_max_info(grouped_old_user_info, users_new_data, period)

    @classmethod
    def get_current_users_stats(
            cls,
            period: str) -> Optional[dict[int, UserStatsForCurrentDay]]:
        users_info = {}
        if period == "day":
            return MDC.authors
        elif period == "week":
            result = UserCurrentStats.fetch_users_current_stats_for_period(UserStatsForCurrentWeek)
        elif period == "month":
            result = UserCurrentStats.fetch_users_current_stats_for_period(UserStatsForCurrentMonth)
        else:
            return

        for user_id, messages, symbols in result:
            users_info[user_id] = UserStatsForCurrentDay(amount_of_symbols=symbols, amount_of_messages=messages)
        return users_info

    @classmethod
    def group_users_stats(cls, messages_info: list, symbols_info: list) -> dict[int, UserStatsForCurrentDay]:
        user_ids = {user_id for stats_info in (messages_info, symbols_info) for user_id, _ in stats_info}
        messages_info = {user_id: amount for user_id, amount in messages_info}
        symbols_info = {user_id: amount for user_id, amount in symbols_info}
        users_info = {}

        for user_id in user_ids:
            amount_of_messages = messages_info.get(user_id, -100)
            amount_of_symbols = symbols_info.get(user_id, -100)
            users_info[user_id] = UserStatsForCurrentDay(
                amount_of_messages=amount_of_messages,
                amount_of_symbols=amount_of_symbols,
            )
        return users_info
