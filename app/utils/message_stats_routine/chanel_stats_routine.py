import aiohttp
import discord

from app import NOTIFICATION_CHANNEL, TOKEN
from app.log import logger
from app.utils import catch_exception
from app.utils.data.channel_stats import ServerStats
from app.utils.message_stats_routine import message_day_counter
from app.utils.webhooks import webhook_sender


class ChanelStats:
    def __init__(self):
        self.symbols_for_month = 0
        self.messages_for_month = 0
        self.symbols_for_week = 0
        self.messages_for_week = 0

    @catch_exception
    async def daily_routine(self):
        logger.info(
            "The daily process of updating server statistics based on the number of messages has started.",
        )
        if not message_day_counter.messages:
            logger.info("No new data for current day")
            return

        logger.info("Collecting daily stats for messages and symbols.")
        messages_champ, symbols_champ = self.collect_stats_for_day()

        logger.info("Updating maximum stats for the day.")
        self.update_max_stats_for_day()
        if NOTIFICATION_CHANNEL is not None:
            logger.info("Sending daily stats message to notification channel.")
            await self.send_message_stats_for_day(messages_champ, symbols_champ)
        logger.info("Successfully updated channel daily stats")

    @catch_exception
    async def weekly_routine(self):
        logger.info(
            "The weekly process of updating server statistics based on the number of messages has started.",
        )

        messages_info, symbols_info = self.collect_stats_for_week()
        if not self.messages_for_week:
            logger.info("No new data for current week")
            return

        logger.info("Updating maximum stats for the week.")
        self.update_max_stats_for_week()

        if NOTIFICATION_CHANNEL is not None:
            logger.info("Sending weekly stats message to notification channel.")
            await self.send_message_stats_for_week(messages_info, symbols_info)

        logger.info("Setting weekly stats to zero after update.")

        self.set_week_current_stats_to_zero()
        logger.info("Successfully updated channel weekly stats")

    @catch_exception
    async def monthly_routine(self):
        logger.info(
            "The monthly process of updating server statistics based on the number of messages has started.",
        )

        messages_info, symbols_info = self.collect_stats_for_month()

        if not self.messages_for_month:
            logger.info("No new data for current month")
            return

        logger.info("Updating maximum stats for the month.")
        self.update_max_stats_for_month()

        if NOTIFICATION_CHANNEL is not None:
            logger.info("Sending monthly stats message to notification channel.")
            await self.send_message_stats_for_month(messages_info, symbols_info)

        logger.info("Setting monthly stats to zero after update.")
        self.set_month_current_stats_to_zero()

        logger.info("Successfully updated channel month stats")

    @staticmethod
    def collect_stats_for_day() -> tuple[tuple[int, int], tuple[int, int]]:
        logger.debug("Collecting stats for today: messages and symbols.")
        messages_champ, symbols_champ = message_day_counter.get_server_champ_for_today()
        logger.debug(
            f"Collected stats - Messages champion: {messages_champ}, Symbols champion: {symbols_champ}",
        )
        return messages_champ, symbols_champ

    def collect_stats_for_week(self) -> tuple[tuple[int, int], tuple[int, int]]:
        logger.debug("Collecting stats for the week.")
        channel_info, messages_info, symbols_info = ServerStats.get_server_stats_for_week()
        self.messages_for_week, self.symbols_for_week = channel_info

        logger.debug(
            f"Collected weekly stats - Messages: {self.messages_for_week}, Symbols: {self.symbols_for_week}",
        )
        return messages_info, symbols_info

    def collect_stats_for_month(self) -> tuple[tuple[int, int], tuple[int, int]]:
        logger.debug("Collecting stats for the month.")
        channel_info, messages_info, symbols_info = ServerStats.get_server_stats_for_month()
        self.messages_for_month, self.symbols_for_month = channel_info

        logger.debug(
            f"Collected monthly stats - Messages: {self.messages_for_month}, Symbols: {self.symbols_for_month}",
        )
        return messages_info, symbols_info

    def update_max_stats_for_day(self):
        self.update_max_stats("day", message_day_counter.messages, message_day_counter.symbols)

    def update_max_stats_for_week(self):
        self.update_max_stats("week", self.messages_for_week, self.symbols_for_week)

    def update_max_stats_for_month(self):
        self.update_max_stats("month", self.messages_for_month, self.symbols_for_month)

    def set_week_current_stats_to_zero(self):
        self.symbols_for_week = 0
        self.messages_for_week = 0
        ServerStats.set_current_stats_for_period_to_zero("week")

    def set_month_current_stats_to_zero(self):
        self.symbols_for_month = 0
        self.messages_for_month = 0
        ServerStats.set_current_stats_for_period_to_zero("month")

    @staticmethod
    def update_max_stats(
        period: str,
        current_amount_of_messages: int,
        current_amount_of_symbols: int,
    ):
        ServerStats.compare_and_update_max_stats(
            period,
            current_amount_of_messages,
            current_amount_of_symbols,
        )

    async def send_message_stats_for_day(
        self,
        messages_info: tuple[int, int],
        symbols_info: tuple[int, int],
    ):
        logger.info("Preparing output message for the daily stats.")
        output = await self.create_output_message(
            channel_info=(message_day_counter.messages, message_day_counter.symbols),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("Всего за день", "Информация по серверу за 24 часа"),
        )
        logger.info("Sending the stats data to webhook.")
        await webhook_sender.send_data(embed=output)
        logger.info("Successfully sent daily stats to the webhook.")

    async def send_message_stats_for_week(
        self,
        messages_info: tuple[int, int],
        symbols_info: tuple[int, int],
    ):
        logger.info("Preparing output message for the weekly stats.")
        output = await self.create_output_message(
            channel_info=(self.messages_for_week, self.symbols_for_week),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("неделю", "Еженедельная информация"),
        )
        logger.info("Sending the weekly stats data to webhook.")

        await webhook_sender.send_data(embed=output)
        logger.info("Successfully sent weekly stats to the webhook.")

    async def send_message_stats_for_month(
        self,
        messages_info: tuple[int, int],
        symbols_info: tuple[int, int],
    ):
        logger.info("Preparing output message for the monthly stats.")
        output = await self.create_output_message(
            channel_info=(self.messages_for_month, self.symbols_for_month),
            messages_info=messages_info,
            symbols_info=symbols_info,
            period_info=("месяц", "Ежемесячная информация"),
        )

        logger.info("Sending the monthly stats data to webhook.")

        await webhook_sender.send_data(embed=output)
        logger.info("Successfully sent weekly stats to the webhook.")

    async def create_output_message(
        self,
        *,
        channel_info: tuple[int, int],
        messages_info: tuple[int, int],
        symbols_info: tuple[int, int],
        period_info: tuple[str, str],
    ) -> discord.Embed:
        user_with_most_symbols, amount_of_symbols_top_user = symbols_info
        user_with_most_messages, amount_of_messages_top_user = messages_info
        amount_of_all_messages, amount_of_all_symbols = channel_info
        name_of_period, description_of_period = period_info

        champ_stats = await self.fetch_user_nickname(
            {user_with_most_messages, user_with_most_symbols},
        )
        user_name_with_most_messages = champ_stats[user_with_most_messages]
        user_name_with_most_symbols = champ_stats[user_with_most_symbols]

        channel_info = (
            f"Кол-во сообщений  =>{amount_of_all_messages}\n"
            f"Кол-во символов  =>{amount_of_all_symbols}"
        )
        message_info = (
            f"Чемпион по сообщениям => {user_name_with_most_messages}\n"
            f"Количество=>{amount_of_messages_top_user}"
        )
        symbol_info = (
            f"Чемпион по символам =>{user_name_with_most_symbols} \n"
            f"Количество => {amount_of_symbols_top_user}"
        )
        info_dict = {
            f"Всего за {name_of_period}": "=" * 25,
            channel_info: "=" * 25,
            message_info: "=" * 25,
            symbol_info: "=" * 25,
        }

        emb = discord.Embed(title=description_of_period, colour=discord.Color.dark_blue())
        for key, value in info_dict.items():
            emb.add_field(name=key, value=value, inline=False)
        return emb

    @staticmethod
    async def fetch_user_nickname(users_id: set[int]) -> dict[int, str]:
        discord_users_url = "https://discord.com/api/users/{}"
        dict_on_names = {}
        headers = {"Authorization": f"Bot {TOKEN}"}

        async with aiohttp.ClientSession() as session:
            for user_id in users_id:
                async with session.get(
                    discord_users_url.format(user_id),
                    headers=headers,
                ) as response:
                    data = await response.json()
                    try:
                        nickname = data["username"]
                    except KeyError:
                        nickname = "No Info"
                    dict_on_names[user_id] = nickname
        return dict_on_names


channel_stats = ChanelStats()
