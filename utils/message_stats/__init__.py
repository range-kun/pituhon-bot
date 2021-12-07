from __future__ import annotations

import re
from types import SimpleNamespace

from configuration import PYTHON_BOT_ID


class UserStats(SimpleNamespace):
    amount_of_symbols: int = 0
    amount_of_messages: int = 0


class MessageCounter:
    messages: int = 0
    symbols: int = 0
    authors: dict[int, UserStats] = {}

    @classmethod
    def set_stats_to_zero(cls):
        cls.messages = 0
        cls.symbols = 0
        cls.authors = {}

    @classmethod
    def proceed_message_info(cls, message):
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

        user_stats = cls.authors.get(message.author.id, UserStats())
        user_stats.amount_of_messages = user_stats.amount_of_messages + 1
        user_stats.amount_of_symbols = user_stats.amount_of_symbols + number_of_symbols_in_string
        cls.authors[message.author.id] = user_stats


class Statistic:
    bot = None

    @classmethod
    def set_bot(cls, bot):
        cls.bot = bot
