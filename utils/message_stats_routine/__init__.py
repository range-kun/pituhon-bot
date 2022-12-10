from __future__ import annotations

import json
import dataclasses
import re


import redis
from redis.commands.json.path import Path

from configuration import REDIS_PORT, REDIS_HOST, REDIS_PASSWORD
from utils import catch_exception


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


@dataclasses.dataclass
class UserStatsForCurrentDay:
    amount_of_symbols: int = 0
    amount_of_messages: int = 0

    def __add__(self, other):
        if isinstance(other, UserStatsForCurrentDay):
            amount_of_symbols = self.amount_of_symbols + other.amount_of_symbols
            amount_of_messages = self.amount_of_messages + other.amount_of_messages
            return UserStatsForCurrentDay(amount_of_messages=amount_of_messages, amount_of_symbols=amount_of_symbols)
        raise TypeError(f"Unsupported type of data {type(other)} for operand +")


class MessageDayCounter:
    _messages: int = 0
    _symbols: int = 0
    _authors: dict[int, UserStatsForCurrentDay] = {}
    redis_connection = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    default_user_stats = UserStatsForCurrentDay()

    @classmethod
    @catch_exception
    async def counter_routine(cls):
        if not cls._messages:
            return
        await cls.save_info_to_redis()
        await cls.set_stats_to_zero()

    @classmethod
    @catch_exception
    async def delete_redis_info(cls):
        cls.redis_connection.delete("symbols", "authors", "messages")

    @classmethod
    async def save_info_to_redis(cls):
        cls.redis_connection.set("messages", cls.messages)
        cls.redis_connection.set("symbols", cls.symbols)
        authors = json.dumps(cls.authors, cls=EnhancedJSONEncoder)
        cls.redis_connection.json().set("authors", Path.rootPath(), authors)

    @classmethod
    async def set_stats_to_zero(cls):
        cls._messages = 0
        cls._symbols = 0
        cls._authors = {}

    @classmethod
    @property
    def messages(cls) -> int:
        redis_messages = cls.redis_connection.get("messages") or 0
        return cls._messages + int(redis_messages)

    @classmethod
    @property
    def symbols(cls) -> int:
        redis_symbols = cls.redis_connection.get("symbols") or 0
        return cls._symbols + int(redis_symbols)

    @classmethod
    @property
    def authors(cls) -> dict[int: UserStatsForCurrentDay]:
        try:
            redis_authors = json.loads(cls.redis_connection.json().get("authors"))
        except TypeError:
            redis_authors = {}

        redis_authors = {int(user_id): UserStatsForCurrentDay(**stats) for user_id, stats in redis_authors.items()}
        users_id = set(redis_authors) | set(cls._authors)

        authors = {}
        for user_id in users_id:
            old_data = redis_authors.get(user_id, cls.default_user_stats)
            current_data = cls._authors.get(user_id, cls.default_user_stats)
            new_data = current_data + old_data
            authors[user_id] = new_data
        return authors

    @classmethod
    def proceed_message_info(cls, message):
        if message.author.bot:
            return
        msg = message.content.lower()

        cls._messages += 1
        sticker_regex = re.compile(r"<:\w+:\d+>")
        if sticker_regex.search(msg):
            number_of_symbols_in_string = 1
            cls._symbols += 1
        else:
            number_of_symbols_in_string = len(msg.replace(" ", ""))
            cls._symbols += len(msg.replace(" ", ""))

        user_stats = cls._authors.get(message.author.id, UserStatsForCurrentDay())
        user_stats.amount_of_messages = user_stats.amount_of_messages + 1
        user_stats.amount_of_symbols = user_stats.amount_of_symbols + number_of_symbols_in_string
        cls._authors[message.author.id] = user_stats

    @classmethod
    def get_server_champ_for_today(cls) -> list[tuple]:
        authors = cls.authors
        user_id_with_most_messages = max(authors, key=lambda user: cls.authors[user].amount_of_messages)
        user_with_most_messages = authors[user_id_with_most_messages].amount_of_messages

        user_id_with_most_symbols = max(authors, key=lambda user: cls.authors[user].amount_of_symbols)
        user_with_most_symbols = authors[user_id_with_most_symbols].amount_of_symbols
        return [(user_id_with_most_messages, user_with_most_messages),
                (user_id_with_most_symbols, user_with_most_symbols)
                ]


class Statistic:
    bot = None

    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot
