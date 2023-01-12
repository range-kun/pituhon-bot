from __future__ import annotations

import dataclasses
import datetime
import json
import re

import redis
from discord import Message
from discord.ext import tasks
from redis.commands.json.path import Path

from app.configuration import REDIS_PORT, REDIS_HOST, REDIS_PASSWORD
from app.log import logger
from app.utils import catch_exception


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


@dataclasses.dataclass
class UserStatsForCurrentDay:
    amount_of_symbols: int = 0
    amount_of_messages: int = 0

    def __add__(self, other: UserStatsForCurrentDay) -> UserStatsForCurrentDay:
        if isinstance(other, UserStatsForCurrentDay):
            amount_of_symbols = self.amount_of_symbols + other.amount_of_symbols
            amount_of_messages = self.amount_of_messages + other.amount_of_messages
            return UserStatsForCurrentDay(amount_of_messages=amount_of_messages, amount_of_symbols=amount_of_symbols)
        raise TypeError(f"Unsupported type of data {type(other)} for operand +")


class MessageDayCounter:
    tz = datetime.datetime.now().astimezone().tzinfo
    execution_time = datetime.time(hour=23, minute=20, tzinfo=tz)

    def __init__(self):
        self._messages = 0
        self._symbols: int = 0
        self._authors: dict[int, UserStatsForCurrentDay] = {}
        self.redis_connection = self.get_redis_connection()
        self.default_user_stats = UserStatsForCurrentDay()

    @staticmethod
    def get_redis_connection():
        connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        try:
            connection.ping()
        except redis.exceptions.TimeoutError:
            logger.warning("Not possible to create connection with remote redis server")
        return connection

    @tasks.loop(minutes=20)
    @catch_exception
    async def counter_routine(self):
        if not self._messages:
            return
        await self.save_info_to_redis()
        logger.debug("Successfully send data to redis")
        self.set_stats_to_zero()

    @tasks.loop(time=execution_time)
    @catch_exception
    async def delete_redis_info(self):
        self.redis_connection.delete("symbols", "authors", "messages")
        logger.info("Data from redis have been set to 0")

    async def save_info_to_redis(self):
        self.redis_connection.set("messages", self.messages)
        self.redis_connection.set("symbols", self.symbols)
        authors = json.dumps(self.authors, cls=EnhancedJSONEncoder)
        self.redis_connection.json().set("authors", Path.root_path(), authors)

    def set_stats_to_zero(self):
        self._messages = 0
        self._symbols = 0
        self._authors = {}

    @property
    def messages(self) -> int:
        redis_messages = self.redis_connection.get("messages") or 0
        return self._messages + int(redis_messages)

    @property
    def symbols(self) -> int:
        redis_symbols = self.redis_connection.get("symbols") or 0
        return self._symbols + int(redis_symbols)

    @property
    def authors(self) -> dict[int: UserStatsForCurrentDay]:
        try:
            redis_authors = json.loads(self.redis_connection.json().get("authors"))
        except TypeError:
            redis_authors = {}

        redis_authors = {int(user_id): UserStatsForCurrentDay(**stats) for user_id, stats in redis_authors.items()}
        users_id = set(redis_authors) | set(self._authors)

        authors = {}
        for user_id in users_id:
            old_data = redis_authors.get(user_id, self.default_user_stats)
            current_data = self._authors.get(user_id, self.default_user_stats)
            new_data = current_data + old_data
            authors[user_id] = new_data
        return authors

    def proceed_message_info(self, message: Message):
        if message.author.bot:
            return
        msg = message.content.lower()

        self._messages += 1
        sticker_regex = re.compile(r"<:\w+:\d+>")
        if sticker_regex.search(msg):
            number_of_symbols_in_string = 1
            self._symbols += 1
        else:
            number_of_symbols_in_string = len(msg.replace(" ", ""))
            self._symbols += len(msg.replace(" ", ""))

        user_stats = self._authors.get(message.author.id, UserStatsForCurrentDay())
        user_stats.amount_of_messages = user_stats.amount_of_messages + 1
        user_stats.amount_of_symbols = user_stats.amount_of_symbols + number_of_symbols_in_string
        self._authors[message.author.id] = user_stats

    def get_server_champ_for_today(self) -> list[tuple]:
        authors = self.authors
        user_id_with_most_messages = max(authors, key=lambda user: self.authors[user].amount_of_messages)
        user_with_most_messages = authors[user_id_with_most_messages].amount_of_messages

        user_id_with_most_symbols = max(authors, key=lambda user: self.authors[user].amount_of_symbols)
        user_with_most_symbols = authors[user_id_with_most_symbols].amount_of_symbols
        return [(user_id_with_most_messages, user_with_most_messages),
                (user_id_with_most_symbols, user_with_most_symbols)
                ]


message_day_counter = MessageDayCounter()


class Statistic:
    bot = None

    def set_bot(self, bot: Bot):
        self.bot = bot
