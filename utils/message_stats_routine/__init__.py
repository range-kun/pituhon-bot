from __future__ import annotations

import re
from types import SimpleNamespace

from configuration import PYTHON_BOT_ID


class UserStatsForCurrentDay(SimpleNamespace):
    amount_of_symbols: int = 0
    amount_of_messages: int = 0

class MessageDayCounter:
    messages: int = 0
    symbols: int = 0
    authors: dict[int, UserStatsForCurrentDay] = {}

    @classmethod
    async def set_stats_to_zero(cls):
        cls.messages = 0
        cls.symbols = 0
        cls.authors = {}

    @classmethod
    def proceed_message_info(cls, message):
        if message.author.bot:
            return
        msg = message.content.lower()
        if message.author.id == PYTHON_BOT_ID:
            return

        cls.messages += 1
        sticker_regex = re.compile(r'<:\w+:\d+>')
        if sticker_regex.search(msg):
            number_of_symbols_in_string = 1
            cls.symbols += 1
        else:
            number_of_symbols_in_string = len(msg.replace(' ', ''))
            cls.symbols += len(msg.replace(' ', ''))

        user_stats = cls.authors.get(message.author.id, UserStatsForCurrentDay())
        user_stats.amount_of_messages = user_stats.amount_of_messages + 1
        user_stats.amount_of_symbols = user_stats.amount_of_symbols + number_of_symbols_in_string
        cls.authors[message.author.id] = user_stats

    @classmethod
    def get_server_champ_for_today(cls) -> list[tuple]:
        user_id_with_most_messages = max(cls.authors, key=lambda user: cls.authors[user].amount_of_messages)
        user_with_most_messages = cls.authors[user_id_with_most_messages].amount_of_messages

        user_id_with_most_symbols = max(cls.authors, key=lambda user: cls.authors[user].amount_of_symbols)
        user_with_most_symbols = cls.authors[user_id_with_most_symbols].amount_of_symbols
        return [(user_id_with_most_messages, user_with_most_messages),
                (user_id_with_most_symbols, user_with_most_symbols)
                ]


class Statistic:
    bot = None

    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot
