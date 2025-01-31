from __future__ import annotations

from app.log import logger
from app.utils import catch_exception
from app.utils.data.user_stats import (
    UserCurrentStats,
    UserMaxStats,
    UserOverallStats,
    UserStatsForCurrentMonth,
    UserStatsForCurrentWeek,
)
from app.utils.message_stats_routine import UserStatsForCurrentDay, message_day_counter


class UserStats:
    @catch_exception
    async def daily_routine(self):
        logger.info(
            "The daily process of updating user statistics based on the number of messages has started.",
        )
        self.update_users_stats_by_end_of_day()
        self.update_user_max_stats_for_period("day")
        logger.info("Successfully updated user daily stats")

    @catch_exception
    async def weekly_routine(self):
        logger.info(
            "The weekly process of updating user statistics based on the number of messages has started.",
        )
        self.update_user_max_stats_for_period("week")
        logger.info("Successfully updated user weekly stats")

    @catch_exception
    async def monthly_routine(self):
        logger.info(
            "The monthly process of updating user statistics based on the number of messages has started.",
        )
        self.update_user_max_stats_for_period("month")
        logger.info("Successfully updated user month stats")

    @staticmethod
    def update_users_stats_by_end_of_day():
        logger.info("Updating user statistics for the week and month.")
        with UserMaxStats.begin() as connect:
            for user_stats_class in [
                UserOverallStats,
                UserStatsForCurrentWeek,
                UserStatsForCurrentMonth,
            ]:
                UserCurrentStats.add_or_update_user_stats(
                    message_day_counter.authors,
                    user_stats_class,
                    connect,
                )

    def update_user_max_stats_for_period(self, period: str):
        logger.info(f"Updating user max statistics for {period}.")
        users_new_data = self.get_current_users_stats(period)
        if not users_new_data:
            logger.info(f"No new data for period {period}")
            return

        logger.info(f"Fetching max users info for the next period: {period}")
        messages_info, symbols_info = UserMaxStats.get_all_users_max_stats(period)

        if messages_info or symbols_info:
            grouped_old_user_info = self.group_users_stats(messages_info, symbols_info)
        else:
            grouped_old_user_info = {}

        logger.info(f"Starting compare_and_update_users_max_info with period: {period}")
        logger.info(
            f"Old data has {len(grouped_old_user_info)} users, new data has {len(users_new_data)} users.",
        )

        try:
            UserMaxStats.compare_and_update_users_max_info(
                grouped_old_user_info,
                users_new_data,
                period,
            )
        except Exception as e:
            logger.error(
                f"Error occurred while comparing and updating users max info for period {period}: {str(e)}",
            )

    @staticmethod
    def get_current_users_stats(period: str) -> dict[int, UserStatsForCurrentDay] | None:
        logger.info(f"Fetching current users info for the next period: {period}")
        users_info = {}
        if period == "day":
            return message_day_counter.authors
        elif period == "week":
            result = UserCurrentStats.fetch_users_current_stats_for_period(UserStatsForCurrentWeek)
        elif period == "month":
            result = UserCurrentStats.fetch_users_current_stats_for_period(UserStatsForCurrentMonth)
        else:
            return

        for user_id, messages, symbols in result:
            users_info[user_id] = UserStatsForCurrentDay(
                amount_of_symbols=symbols,
                amount_of_messages=messages,
            )
        return users_info

    @staticmethod
    def group_users_stats(
        messages_info: list,
        symbols_info: list,
    ) -> dict[int, UserStatsForCurrentDay]:
        user_ids = {
            user_id for stats_info in (messages_info, symbols_info) for user_id, _ in stats_info
        }
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


user_stats = UserStats()
